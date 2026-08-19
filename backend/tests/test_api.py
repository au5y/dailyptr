import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app import auth, models
from app.database import SessionLocal
from app.main import app

from .solutions import SOLUTIONS_BY_TITLE

# 2024-01-01 was a Monday, so this week gives one date per weekday tier
# (Mon/Tue=easy, Wed/Thu=medium, Fri/Sat=hard, Sun=expert). All in the past
# relative to "today" so get_or_create_day's future-date guard never trips.
WEEK_START = date(2024, 1, 1)


def _quiz_answers_for(day_id: int) -> dict[int, int]:
    """Look up the correct index straight from the DB (the API never exposes it)."""
    db = SessionLocal()
    try:
        day = db.get(models.Day, day_id)
        answers = {}
        for qid in day.quiz_question_ids:
            q = db.get(models.QuizQuestion, qid)
            answers[qid] = q.correct_index
        return answers
    finally:
        db.close()


def test_today_endpoint_returns_a_full_challenge(client):
    resp = client.get("/api/today")
    assert resp.status_code == 200
    body = resp.json()
    assert body["day"]["date"] == date.today().isoformat()
    assert len(body["quiz"]) == 3
    assert "id" in body["coding"]
    assert "prompt" in body["concept"]
    # correct_index must never leak to the client
    assert "correct_index" not in body["quiz"][0]


def test_future_day_is_rejected(client):
    future = (date.today() + timedelta(days=3)).isoformat()
    resp = client.get(f"/api/day/{future}")
    assert resp.status_code == 400


def test_full_week_end_to_end_flow(client):
    for i in range(7):
        d = WEEK_START + timedelta(days=i)
        resp = client.get(f"/api/day/{d.isoformat()}")
        assert resp.status_code == 200, resp.text
        challenge = resp.json()
        day_id = challenge["day"]["id"]
        expected_difficulty = ["easy", "easy", "medium", "medium", "hard", "hard", "expert"][i]
        assert challenge["day"]["difficulty"] == expected_difficulty

        # 1. quiz - answer everything correctly
        answers = _quiz_answers_for(day_id)
        quiz_resp = client.post(f"/api/quiz/{day_id}/submit", json={"answers": answers})
        assert quiz_resp.status_code == 200, quiz_resp.text
        quiz_result = quiz_resp.json()
        assert quiz_result["correct"] == quiz_result["total"] == 3
        assert quiz_result["points_awarded"] > 0

        # resubmitting should be rejected
        assert client.post(f"/api/quiz/{day_id}/submit", json={"answers": answers}).status_code == 400

        # 2. coding - submit the known-correct solution for whichever problem was assigned
        title = challenge["coding"]["title"]
        code_resp = client.post(f"/api/coding/{day_id}/submit", json={"code": SOLUTIONS_BY_TITLE[title]})
        assert code_resp.status_code == 200, code_resp.text
        code_result = code_resp.json()
        assert code_result["passed"] is True
        assert code_result["points_awarded"] > 0

        # 3. concept check - mark as understood
        concept_resp = client.post(f"/api/concept/{day_id}/submit", json={"self_rating_correct": True})
        assert concept_resp.status_code == 200, concept_resp.text
        assert concept_resp.json()["points_awarded"] > 0

        # day should now be fully completed
        refreshed = client.get(f"/api/day/{d.isoformat()}").json()
        assert refreshed["day"]["fully_completed"] is True
        assert refreshed["day"]["points_earned"] > 0

    stats = client.get("/api/stats").json()
    assert stats["days_completed"] >= 7
    assert stats["total_points"] > 0


def test_bad_coding_submission_does_not_complete_the_day(client):
    d = date(2024, 2, 5)  # a Monday not touched by the full-week test
    challenge = client.get(f"/api/day/{d.isoformat()}").json()
    day_id = challenge["day"]["id"]

    resp = client.post(f"/api/coding/{day_id}/submit", json={"code": "not valid c++"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is False
    assert body["points_awarded"] == 0

    refreshed = client.get(f"/api/day/{d.isoformat()}").json()
    assert refreshed["day"]["coding_completed"] is False


def _logged_in_client() -> TestClient:
    c = TestClient(app)
    db = SessionLocal()
    try:
        unique = uuid.uuid4().hex[:8]
        user = models.User(google_sub=f"test-sub-{unique}", email=f"test-{unique}@example.com", name=f"Test {unique}")
        db.add(user)
        db.commit()
        db.refresh(user)
    finally:
        db.close()
    c.cookies.set(auth.COOKIE_NAME, auth.make_session_cookie(user.id))
    return c


def test_unauthenticated_api_request_is_rejected():
    c = TestClient(app)
    resp = c.get("/api/today")
    assert resp.status_code == 401


def test_find_or_create_google_user_is_idempotent_per_sub():
    db = SessionLocal()
    try:
        sub = f"test-sub-{uuid.uuid4().hex[:8]}"
        first, first_created = auth.find_or_create_google_user(db, sub, "a@example.com", "A")
        second, second_created = auth.find_or_create_google_user(db, sub, "a@example.com", "A")
        assert first.id == second.id
        assert first_created is True
        assert second_created is False
    finally:
        db.close()


def test_two_users_get_independent_days_for_same_date_and_track():
    d = date(2024, 3, 4)  # untouched by other tests
    alice, bob = _logged_in_client(), _logged_in_client()

    alice_day = alice.get(f"/api/day/{d.isoformat()}").json()["day"]
    bob_day = bob.get(f"/api/day/{d.isoformat()}").json()["day"]

    assert alice_day["id"] != bob_day["id"]

    answers = _quiz_answers_for(alice_day["id"])
    alice.post(f"/api/quiz/{alice_day['id']}/submit", json={"answers": answers})

    bob_day_after = bob.get(f"/api/day/{d.isoformat()}").json()["day"]
    assert bob_day_after["quiz_completed"] is False


def test_new_user_is_not_onboarded_until_onboarding_completes(client):
    assert client.get("/api/me").json()["onboarded"] is False
    tracks_before = {t["id"]: t["subscribed"] for t in client.get("/api/tracks").json()}
    assert not any(tracks_before.values())

    resp = client.post("/api/onboarding", json={"tracks": ["cpp_core", "html_css"]})
    assert resp.status_code == 200
    subscribed = {t["id"] for t in resp.json() if t["subscribed"]}
    assert subscribed == {"cpp_core", "html_css"}
    assert client.get("/api/me").json()["onboarded"] is True

    # backfilled history should now exist for a subscribed track...
    assert len(client.get("/api/history?track=cpp_core").json()) > 1
    # ...but not for one the user never picked
    assert client.get("/api/history?track=system_design").json() == []


def test_onboarding_requires_at_least_one_topic(client):
    resp = client.post("/api/onboarding", json={"tracks": []})
    assert resp.status_code == 400


def test_subscribe_adds_a_track_after_onboarding(client):
    client.post("/api/onboarding", json={"tracks": ["cpp_core"]})
    resp = client.post("/api/subscribe", json={"track": "system_design"})
    assert resp.status_code == 200
    subscribed = {t["id"] for t in resp.json() if t["subscribed"]}
    assert subscribed == {"cpp_core", "system_design"}


def test_backfilled_days_before_subscription_are_bonus_not_missed(client):
    """/api/today's backfill (via onboarding) creates ~30 days of history
    ending today; every one of those except today itself predates "today" as
    the subscription date, so they should read as bonus, not late/missed."""
    client.post("/api/onboarding", json={"tracks": ["cpp_core"]})
    history = client.get("/api/history?track=cpp_core").json()
    past_days = [d for d in history if d["date"] != date.today().isoformat()]
    assert past_days  # backfill actually produced older days
    assert all(d["is_bonus"] and not d["is_late"] for d in past_days)

    stats = client.get("/api/stats?track=cpp_core").json()
    assert stats["days_missed_open"] == 0


def test_cannot_act_on_another_users_day():
    d = date(2024, 3, 5)  # untouched by other tests
    alice, bob = _logged_in_client(), _logged_in_client()
    alice_day_id = alice.get(f"/api/day/{d.isoformat()}").json()["day"]["id"]

    assert bob.post(f"/api/day/{alice_day_id}/reset").status_code == 404
    assert bob.post(f"/api/quiz/{alice_day_id}/submit", json={"answers": {}}).status_code == 404
    assert bob.post(f"/api/coding/{alice_day_id}/submit", json={"code": "x"}).status_code == 404
    assert bob.post(f"/api/concept/{alice_day_id}/submit", json={"self_rating_correct": True}).status_code == 404

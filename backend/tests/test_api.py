import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app import auth, models
from app.database import SessionLocal
from app.main import app

# 2024-01-01 was a Monday, so this week gives one date per weekday tier
# (Mon/Tue=easy, Wed/Thu=medium, Fri/Sat=hard, Sun=expert). All in the past
# relative to "today" so get_or_create_day's future-date guard never trips.
WEEK_START = date(2024, 1, 1)


def _quiz_question_ids_and_correct(day_id: int) -> list[tuple[int, int]]:
    """[(question_id, correct_index), ...] for a day's quiz, looked up straight
    from the DB (the API never exposes correct_index before it's answered)."""
    db = SessionLocal()
    try:
        day = db.get(models.Day, day_id)
        return [(qid, db.get(models.QuizQuestion, qid).correct_index) for qid in day.quiz_question_ids]
    finally:
        db.close()


def _answer_quiz_correctly(client: TestClient, day_id: int):
    """Answers every question of a day's quiz correctly, one at a time (the
    only way the API allows), and returns the quiz-completing response."""
    resp = None
    for qid, correct_index in _quiz_question_ids_and_correct(day_id):
        resp = client.post(f"/api/quiz/{day_id}/question/{qid}/answer", json={"choice_index": correct_index})
        assert resp.status_code == 200, resp.text
    return resp


def _correct_code_review_matches(day_id: int) -> list[dict]:
    """[{"line", "reason"}, ...] for every issue in a day's code review
    challenge, looked up straight from the DB (the API never exposes which
    lines/reasons are correct before grading)."""
    db = SessionLocal()
    try:
        day = db.get(models.Day, day_id)
        challenge = db.get(models.CodeReviewChallenge, day.code_review_challenge_id)
        return [{"line": issue["line"], "reason": issue["reason"]} for issue in challenge.issues]
    finally:
        db.close()


def _correct_critical_reasoning_matches(day_id: int) -> list[dict]:
    """[{"line", "reason"}, ...] for every issue in a day's critical reasoning
    challenge, looked up straight from the DB, same idea as
    _correct_code_review_matches."""
    db = SessionLocal()
    try:
        day = db.get(models.Day, day_id)
        challenge = db.get(models.CriticalReasoningChallenge, day.critical_reasoning_challenge_id)
        return [{"line": issue["line"], "reason": issue["reason"]} for issue in challenge.issues]
    finally:
        db.close()


def test_today_endpoint_returns_a_full_challenge(client):
    resp = client.get("/api/today")
    assert resp.status_code == 200
    body = resp.json()
    assert body["day"]["date"] == date.today().isoformat()
    assert len(body["quiz"]) == 3
    assert "id" in body["code_review"]
    assert "prompt" in body["concept"]
    # correct_index must never leak to the client
    assert "correct_index" not in body["quiz"][0]


def test_future_day_is_rejected(client):
    future = (date.today() + timedelta(days=3)).isoformat()
    resp = client.get(f"/api/day/{future}")
    assert resp.status_code == 400


def _complete_day(client: TestClient, d: date) -> dict:
    """Fully completes one day (quiz, code review, concept) and returns the
    final component's response body, so the caller can inspect e.g.
    milestones_hit on whichever submission actually finished the day."""
    day_id = client.get(f"/api/day/{d.isoformat()}").json()["day"]["id"]
    _answer_quiz_correctly(client, day_id)
    matches = _correct_code_review_matches(day_id)
    client.post(f"/api/code-review/{day_id}/submit", json={"matches": matches})
    resp = client.post(f"/api/concept/{day_id}/submit", json={"self_rating_correct": True})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_streak_milestone_awarded_once_at_threshold(client):
    # 3 consecutive days ending today - the first one to complete a real
    # (non-backfilled) 3-day streak, so it should hit the 3-day milestone
    # exactly once, on the 3rd day's completion.
    day1, day2, today = [date.today() - timedelta(days=n) for n in (2, 1, 0)]

    result1 = _complete_day(client, day1)
    assert result1["milestones_hit"] == []
    result2 = _complete_day(client, day2)
    assert result2["milestones_hit"] == []
    result3 = _complete_day(client, today)
    assert result3["milestones_hit"] == [3]
    assert result3["points_awarded"] > 0

    stats = client.get("/api/stats").json()
    assert stats["current_streak"] == 3
    assert stats["badges"] == [3]

    # resetting and re-completing today shouldn't re-award the same milestone
    day_id = client.get(f"/api/day/{today.isoformat()}").json()["day"]["id"]
    client.post(f"/api/day/{day_id}/reset")
    result_again = _complete_day(client, today)
    assert result_again["milestones_hit"] == []
    assert client.get("/api/stats").json()["badges"] == [3]


def test_full_week_end_to_end_flow(client):
    for i in range(7):
        d = WEEK_START + timedelta(days=i)
        resp = client.get(f"/api/day/{d.isoformat()}")
        assert resp.status_code == 200, resp.text
        challenge = resp.json()
        day_id = challenge["day"]["id"]
        expected_difficulty = ["easy", "easy", "medium", "medium", "hard", "hard", "expert"][i]
        assert challenge["day"]["difficulty"] == expected_difficulty

        # 1. quiz - answer everything correctly, one question at a time
        quiz_result = _answer_quiz_correctly(client, day_id).json()
        assert quiz_result["quiz_completed"] is True
        assert quiz_result["quiz_correct"] == quiz_result["quiz_total"] == 3
        assert quiz_result["points_awarded"] > 0

        # answering again once the quiz is completed should be rejected
        qid, correct_index = _quiz_question_ids_and_correct(day_id)[0]
        resp = client.post(f"/api/quiz/{day_id}/question/{qid}/answer", json={"choice_index": correct_index})
        assert resp.status_code == 400

        # 2. code review - flag every real issue's line with its real reason
        matches = _correct_code_review_matches(day_id)
        code_review_resp = client.post(f"/api/code-review/{day_id}/submit", json={"matches": matches})
        assert code_review_resp.status_code == 200, code_review_resp.text
        code_review_result = code_review_resp.json()
        assert code_review_result["correct_count"] == code_review_result["total"] == len(matches)
        assert code_review_result["points_awarded"] > 0

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


def test_code_review_wrong_matches_award_no_points(client):
    d = date(2024, 2, 5)  # a Monday not touched by the full-week test
    challenge = client.get(f"/api/day/{d.isoformat()}").json()
    day_id = challenge["day"]["id"]

    # A line number no snippet is 500 lines long, paired with a reason that's
    # never the right one for it - guaranteed to match zero issues.
    resp = client.post(f"/api/code-review/{day_id}/submit", json={"matches": [{"line": 500, "reason": "nope"}]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["correct_count"] == 0
    assert body["points_awarded"] == 0

    # unlike quiz, code review completes either way (there's no retry once
    # submitted) - only the points differ based on how many matches land.
    refreshed = client.get(f"/api/day/{d.isoformat()}").json()
    assert refreshed["day"]["code_review_completed"] is True
    assert refreshed["day"]["code_review_correct"] == 0

    # resubmitting is rejected, same as the quiz
    resp2 = client.post(f"/api/code-review/{day_id}/submit", json={"matches": []})
    assert resp2.status_code == 400


def test_system_design_day_uses_critical_reasoning_not_code_review(client):
    """system_design's review_kind is "reasoning" (see config.TRACKS) - its
    days should carry a critical_reasoning challenge, not a code_review one,
    and completing it (not code review) should be what finishes the day."""
    d = date(2024, 4, 1)  # untouched by other tests
    challenge = client.get(f"/api/day/{d.isoformat()}?track=system_design").json()
    day_id = challenge["day"]["id"]
    assert challenge["code_review"] is None
    assert "id" in challenge["critical_reasoning"]

    _answer_quiz_correctly(client, day_id)
    matches = _correct_critical_reasoning_matches(day_id)
    cr_resp = client.post(f"/api/critical-reasoning/{day_id}/submit", json={"matches": matches})
    assert cr_resp.status_code == 200, cr_resp.text
    cr_result = cr_resp.json()
    assert cr_result["correct_count"] == cr_result["total"] == len(matches)
    assert cr_result["points_awarded"] > 0

    concept_resp = client.post(f"/api/concept/{day_id}/submit", json={"self_rating_correct": True})
    assert concept_resp.status_code == 200, concept_resp.text

    refreshed = client.get(f"/api/day/{d.isoformat()}?track=system_design").json()
    assert refreshed["day"]["fully_completed"] is True
    assert refreshed["day"]["critical_reasoning_completed"] is True
    # code review's endpoint should refuse a track that doesn't use it
    other_day_id = client.get(f"/api/day/{(d + timedelta(days=1)).isoformat()}?track=system_design").json()["day"]["id"]
    assert client.post(f"/api/code-review/{other_day_id}/submit", json={"matches": []}).status_code == 400


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

    _answer_quiz_correctly(alice, alice_day["id"])

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
    assert bob.post(f"/api/quiz/{alice_day_id}/question/1/answer", json={"choice_index": 0}).status_code == 404
    assert bob.post(f"/api/code-review/{alice_day_id}/submit", json={"matches": []}).status_code == 404
    assert bob.post(f"/api/concept/{alice_day_id}/submit", json={"self_rating_correct": True}).status_code == 404

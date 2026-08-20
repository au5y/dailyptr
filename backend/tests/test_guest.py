from datetime import date

from app import models
from app.database import SessionLocal
from app.day_service import select_day_content


def _quiz_ids_and_correct(d: date, track: str) -> list[tuple[int, int]]:
    db = SessionLocal()
    try:
        content = select_day_content(db, d, track)
        return [(qid, db.get(models.QuizQuestion, qid).correct_index) for qid in content.quiz_question_ids]
    finally:
        db.close()


def _review_matches(d: date, track: str) -> tuple[str, list[dict]]:
    """(review_kind, matches) for a (date, track)'s review challenge."""
    db = SessionLocal()
    try:
        from app import config
        content = select_day_content(db, d, track)
        review_kind = config.TRACKS[track]["review_kind"]
        model = models.CodeReviewChallenge if review_kind == "code" else models.CriticalReasoningChallenge
        challenge = db.get(model, content.review_challenge_id)
        return review_kind, [{"line": i["line"], "reason": i["reason"]} for i in challenge.issues]
    finally:
        db.close()


def _day_count(track: str) -> int:
    db = SessionLocal()
    try:
        return db.query(models.Day).filter(models.Day.track == track).count()
    finally:
        db.close()


def test_select_day_content_matches_get_or_create_day(client):
    d = date(2024, 5, 6)  # a Monday, untouched by other tests
    real_day = client.get(f"/api/day/{d.isoformat()}").json()["day"]

    content = None
    db = SessionLocal()
    try:
        content = select_day_content(db, d, "cpp_core")
    finally:
        db.close()

    assert content.difficulty == real_day["difficulty"]
    assert content.weekday == real_day["weekday"]


def test_guest_challenge_matches_real_day_and_creates_no_day_row(guest_client):
    d = date(2024, 5, 7)  # a Tuesday, untouched by other tests
    before = _day_count("cpp_core")

    resp = guest_client.get(f"/api/guest/challenge?date={d.isoformat()}&track=cpp_core")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["day"]["date"] == d.isoformat()
    assert body["day"]["track"] == "cpp_core"
    assert len(body["quiz"]) == 3
    assert "id" in body["code_review"]
    assert body["critical_reasoning"] is None
    assert "prompt" in body["concept"]
    assert "correct_index" not in body["quiz"][0]

    assert _day_count("cpp_core") == before  # no Day row was created


def test_guest_challenge_matches_system_design_critical_reasoning(guest_client):
    d = date(2024, 5, 8)
    resp = guest_client.get(f"/api/guest/challenge?date={d.isoformat()}&track=system_design")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code_review"] is None
    assert "id" in body["critical_reasoning"]


def test_guest_challenge_rejects_future_date(guest_client):
    from datetime import timedelta
    future = (date.today() + timedelta(days=3)).isoformat()
    resp = guest_client.get(f"/api/guest/challenge?date={future}&track=cpp_core")
    assert resp.status_code == 400


def test_guest_endpoints_reject_non_guest_users(client):
    d = date(2024, 5, 9)
    resp = client.get(f"/api/guest/challenge?date={d.isoformat()}&track=cpp_core")
    assert resp.status_code == 403


def test_guest_quiz_answer_is_stateless_and_repeatable(guest_client):
    d = date(2024, 5, 10)
    qid, correct_index = _quiz_ids_and_correct(d, "cpp_core")[0]
    before = _day_count("cpp_core")

    for _ in range(2):  # repeatable - no persisted "already answered" state
        resp = guest_client.post("/api/guest/quiz/answer", json={
            "date": d.isoformat(), "track": "cpp_core", "question_id": qid, "choice_index": correct_index,
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["correct"] is True
        assert body["correct_index"] == correct_index

    assert _day_count("cpp_core") == before  # no Day row ever created


def test_guest_code_review_check_matches_live_grading(guest_client):
    d = date(2024, 5, 11)  # untouched by other tests, weekday picked to land on cpp_core
    review_kind, matches = _review_matches(d, "cpp_core")
    assert review_kind == "code"

    resp = guest_client.post("/api/guest/code-review/check", json={
        "date": d.isoformat(), "track": "cpp_core", "matches": matches,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["correct_count"] == body["total"] == len(matches)
    assert body["points_awarded"] > 0
    assert body["milestones_hit"] == []


def test_guest_critical_reasoning_check_matches_live_grading(guest_client):
    d = date(2024, 5, 12)
    review_kind, matches = _review_matches(d, "system_design")
    assert review_kind == "reasoning"

    resp = guest_client.post("/api/guest/critical-reasoning/check", json={
        "date": d.isoformat(), "track": "system_design", "matches": matches,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["correct_count"] == body["total"] == len(matches)
    assert body["points_awarded"] > 0
    assert body["milestones_hit"] == []

    # wrong track for this challenge kind is rejected
    resp2 = guest_client.post("/api/guest/code-review/check", json={
        "date": d.isoformat(), "track": "system_design", "matches": matches,
    })
    assert resp2.status_code == 400


def test_guest_concept_score(guest_client):
    d = date(2024, 5, 13)
    before = _day_count("cpp_core")

    resp = guest_client.post("/api/guest/concept/score", json={
        "date": d.isoformat(), "track": "cpp_core", "self_rating_correct": True,
    })
    assert resp.status_code == 200, resp.text
    assert resp.json()["points_awarded"] > 0

    resp2 = guest_client.post("/api/guest/concept/score", json={
        "date": d.isoformat(), "track": "cpp_core", "self_rating_correct": False,
    })
    assert resp2.json()["points_awarded"] == 0

    assert _day_count("cpp_core") == before  # no Day row created by either call

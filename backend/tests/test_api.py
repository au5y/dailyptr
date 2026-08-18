from datetime import date, timedelta

from app import models
from app.database import SessionLocal

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

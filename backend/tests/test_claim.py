from datetime import date, timedelta

from app import models
from app.database import SessionLocal

from .test_guest import _quiz_ids_and_correct, _review_matches


def _full_claim_day(d: date, track: str) -> dict:
    """A ClaimDayIn payload that fully completes `d` for `track` (all quiz
    questions correct, review fully matched, concept self-rated correct)."""
    quiz_answers = {str(qid): correct for qid, correct in _quiz_ids_and_correct(d, track)}
    review_kind, matches = _review_matches(d, track)
    day_in = {
        "track": track,
        "date": d.isoformat(),
        "quiz_answers": quiz_answers,
        "concept_self_rating": True,
    }
    if review_kind == "code":
        day_in["code_review_matches"] = matches
    else:
        day_in["critical_reasoning_matches"] = matches
    return day_in


def test_claim_replays_a_full_local_history_with_streak_and_milestone(client):
    # 3 consecutive days ending today - the first real (non-backfilled)
    # 3-day streak, so claiming should hit the 3-day milestone exactly once,
    # same as if the user had played live day by day (see test_api.py's
    # test_streak_milestone_awarded_once_at_threshold for the live-play version).
    day1, day2, today = [date.today() - timedelta(days=n) for n in (2, 1, 0)]

    resp = client.post("/api/claim", json={
        "subscriptions": [{"track": "cpp_core", "subscribed_at": day1.isoformat()}],
        "days": [_full_claim_day(day1, "cpp_core"), _full_claim_day(day2, "cpp_core"), _full_claim_day(today, "cpp_core")],
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["claimed_days"]) == 3
    assert body["skipped_days"] == []
    assert body["claimed_subscriptions"] == ["cpp_core"]
    assert all(d["fully_completed"] for d in body["claimed_days"])

    stats = client.get("/api/stats?track=cpp_core").json()
    assert stats["current_streak"] == 3
    assert stats["badges"] == [3]


def test_claim_skips_days_and_subscription_the_account_already_has(client):
    d = date(2024, 6, 1)  # untouched by other tests
    # play this day live first, so the account already has it
    live_day = client.get(f"/api/day/{d.isoformat()}").json()["day"]
    client.post("/api/subscribe", json={"track": "cpp_core"})  # already onboarded via `client` fixture defaults

    resp = client.post("/api/claim", json={
        "subscriptions": [{"track": "cpp_core", "subscribed_at": d.isoformat()}],
        "days": [_full_claim_day(d, "cpp_core")],
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["claimed_days"] == []
    assert body["skipped_days"] == [{"track": "cpp_core", "date": d.isoformat(), "reason": "account already has this day"}]
    assert body["skipped_subscriptions"] == ["cpp_core"]

    # the pre-existing day's own state (untouched, still incomplete) is unaffected
    db = SessionLocal()
    try:
        day = db.get(models.Day, live_day["id"])
        assert day.quiz_completed is False
    finally:
        db.close()


def test_claim_is_idempotent(client):
    d = date(2024, 6, 2)
    payload = {
        "subscriptions": [{"track": "cpp_core", "subscribed_at": d.isoformat()}],
        "days": [_full_claim_day(d, "cpp_core")],
    }
    first = client.post("/api/claim", json=payload)
    assert len(first.json()["claimed_days"]) == 1

    second = client.post("/api/claim", json=payload)
    body = second.json()
    assert body["claimed_days"] == []
    assert body["skipped_days"] == [{"track": "cpp_core", "date": d.isoformat(), "reason": "account already has this day"}]
    assert body["skipped_subscriptions"] == ["cpp_core"]

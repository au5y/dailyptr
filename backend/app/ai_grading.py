"""
Optional AI grading for concept-check free responses, via the Anthropic API.
Only used if ANTHROPIC_API_KEY is set (see config.py) - the app works fine
without it, falling back to the plain self-graded "Got it / Missed it" flow.
"""
import json

from anthropic import Anthropic

from . import config

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    if _client is None:
        _client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


GRADE_SYSTEM_PROMPT = (
    "You are grading a student's free-response answer to a C++ concept-check question "
    "against a reference model answer. Be lenient on wording and phrasing - the student "
    "does not need to match the model answer's language, only demonstrate they understand "
    "the core idea(s). Respond with ONLY a JSON object, no other text, no markdown fences: "
    '{"correct": true or false, "feedback": "1-3 sentences, specific and encouraging, '
    'pointing out anything important they missed"}'
)


def grade_concept(prompt: str, model_answer: str, user_notes: str) -> tuple[bool, str]:
    client = _get_client()
    message = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=300,
        system=GRADE_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Question:\n{prompt}\n\n"
                f"Reference model answer:\n{model_answer}\n\n"
                f"Student's answer:\n{user_notes}\n\n"
                "Grade the student's answer now."
            ),
        }],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    return bool(data["correct"]), str(data.get("feedback", ""))

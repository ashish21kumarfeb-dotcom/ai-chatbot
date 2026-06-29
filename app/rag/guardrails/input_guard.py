import re
from dataclasses import dataclass, asdict


MAX_QUERY_LENGTH = 2000


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str
    user_message: str
    safe_question: str

    def to_dict(self) -> dict:
        return asdict(self)


PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(the\s+)?above\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"show\s+(your\s+)?system\s+prompt",
    r"print\s+(your\s+)?system\s+prompt",
    r"what\s+is\s+(your\s+)?system\s+prompt",
    r"developer\s+message",
    r"hidden\s+instructions",
    r"internal\s+instructions",
    r"chain\s+of\s+thought",
    r"show\s+your\s+reasoning\s+steps\s+verbatim",
    r"jailbreak",
    r"\bDAN\b",
    r"api\s+key",
    r"secret\s+key",
    r"environment\s+variables",
    r"\.env",
]


def _contains_prompt_injection(text: str) -> bool:
    lowered = text.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return True

    return False


def validate_user_question(question: str) -> GuardrailResult:
    cleaned_question = (question or "").strip()

    if not cleaned_question:
        return GuardrailResult(
            allowed=False,
            reason="empty_question",
            user_message="Please ask a valid question about the uploaded documents.",
            safe_question="",
        )

    if len(cleaned_question) > MAX_QUERY_LENGTH:
        return GuardrailResult(
            allowed=False,
            reason="query_too_long",
            user_message="Your question is too long. Please ask a shorter, focused question.",
            safe_question="",
        )

    if _contains_prompt_injection(cleaned_question):
        return GuardrailResult(
            allowed=False,
            reason="prompt_injection_or_secret_request",
            user_message=(
                "I can answer questions from uploaded documents, "
                "but I can’t reveal or override system instructions."
            ),
            safe_question="",
        )

    return GuardrailResult(
        allowed=True,
        reason="passed",
        user_message="",
        safe_question=cleaned_question,
    )
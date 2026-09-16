import re
from dataclasses import dataclass

INJECTION_PATTERNS = (
    (
        "ignore_previous_instructions",
        re.compile(
            r"\bignore\s+(all\s+|any\s+)?previous\s+instructions?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ignore_system_instructions",
        re.compile(
            r"\bignore\s+(the\s+)?system\s+(prompt|instructions?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reveal_system_prompt",
        re.compile(
            r"\b(reveal|show|print|display|repeat)\b.{0,30}"
            r"\b(system|developer)\s+(prompt|message|instructions?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "jailbreak_attempt",
        re.compile(
            r"\b(jailbreak|developer\s+mode|dan\s+mode)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "override_policy",
        re.compile(
            r"\b(bypass|disable|override)\b.{0,30}"
            r"\b(policy|guardrail|security|restriction)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class PromptGuardrailResult:
    allowed: bool
    reason: str
    detections: tuple[str, ...]


def scan_prompt(prompt: str) -> PromptGuardrailResult:
    detections = tuple(
        name
        for name, pattern in INJECTION_PATTERNS
        if pattern.search(prompt)
    )

    if detections:
        return PromptGuardrailResult(
            allowed=False,
            reason="Potential prompt-injection attempt detected",
            detections=detections,
        )

    return PromptGuardrailResult(
        allowed=True,
        reason="Prompt passed security inspection",
        detections=(),
    )

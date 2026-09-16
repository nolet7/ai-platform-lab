import re
from dataclasses import dataclass

PII_PATTERNS = {
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "ssn": re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    ),
    "phone": re.compile(
        r"(?<!\d)"
        r"(?:\+1[-.\s]?)?"
        r"(?:\(?\d{3}\)?[-.\s]?)"
        r"\d{3}[-.\s]?\d{4}"
        r"(?!\d)"
    ),
}


REPLACEMENTS = {
    "email": "[REDACTED_EMAIL]",
    "ssn": "[REDACTED_SSN]",
    "phone": "[REDACTED_PHONE]",
}


@dataclass(frozen=True)
class PIIRedactionResult:
    text: str
    detected: bool
    count: int
    pii_types: tuple[str, ...]


def redact_pii(text: str) -> PIIRedactionResult:
    redacted = text
    total_count = 0
    detected_types: list[str] = []

    for pii_type, pattern in PII_PATTERNS.items():
        redacted, count = pattern.subn(
            REPLACEMENTS[pii_type],
            redacted,
        )

        if count:
            total_count += count
            detected_types.append(pii_type)

    return PIIRedactionResult(
        text=redacted,
        detected=total_count > 0,
        count=total_count,
        pii_types=tuple(detected_types),
    )

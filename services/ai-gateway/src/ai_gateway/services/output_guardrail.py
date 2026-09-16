from dataclasses import dataclass

from ai_gateway.services.pii import redact_pii


@dataclass(frozen=True)
class OutputGuardrailResult:
    text: str
    modified: bool
    redaction_count: int


def protect_output(text: str) -> OutputGuardrailResult:
    pii_result = redact_pii(text)

    return OutputGuardrailResult(
        text=pii_result.text,
        modified=pii_result.detected,
        redaction_count=pii_result.count,
    )

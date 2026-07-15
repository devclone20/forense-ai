"""
Case state machine.

Encodes the complete transition graph and validation rules.
This module has zero I/O — it is a pure domain object, fully unit-testable.
"""

from dataclasses import dataclass


# ── Transition graph ──────────────────────────────────────────────────────────

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "aberto": ["em_investigacao"],
    "em_investigacao": ["em_revisao", "aberto"],
    "em_revisao": ["fechado", "em_investigacao"],
    "fechado": ["arquivado", "em_investigacao"],
    "arquivado": [],  # terminal — only admin can reopen via override
}

# Backward transitions that require a written justification
REQUIRES_JUSTIFICATION: set[tuple[str, str]] = {
    ("em_investigacao", "aberto"),
    ("em_revisao", "em_investigacao"),
    ("fechado", "em_investigacao"),
}

# Transitions that mark terminal timestamps on the case
SETS_CLOSED_AT: set[str] = {"fechado"}
SETS_ARCHIVED_AT: set[str] = {"arquivado"}
CLEARS_CLOSED_AT: set[tuple[str, str]] = {
    ("fechado", "em_investigacao"),
}


# ── Error types ───────────────────────────────────────────────────────────────

class TransitionError(ValueError):
    """Raised when a requested transition is not allowed."""


class JustificationRequired(TransitionError):
    """Raised when a backward transition lacks a justification."""


# ── Validation ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TransitionResult:
    from_status: str
    to_status: str
    requires_justification: bool
    sets_closed_at: bool
    sets_archived_at: bool
    clears_closed_at: bool


def validate_transition(
    from_status: str,
    to_status: str,
    justification: str | None = None,
    is_admin: bool = False,
) -> TransitionResult:
    """
    Validate a requested case state transition.

    Args:
        from_status: Current case status.
        to_status: Desired new status.
        justification: Written justification (required for some backward transitions).
        is_admin: Whether the requesting user is an admin (can reopen archived cases).

    Returns:
        TransitionResult describing what side effects should be applied.

    Raises:
        TransitionError: If the transition is not allowed.
        JustificationRequired: If justification is missing for a backward transition.
    """
    # Terminal state: only admins may reopen
    if from_status == "arquivado":
        if not is_admin:
            raise TransitionError(
                "Cannot transition out of 'arquivado' — only admins may reopen archived cases."
            )
        # Admin override: allow transition to any non-terminal state
        allowed = ["fechado", "em_revisao", "em_investigacao", "aberto"]
        if to_status not in allowed:
            raise TransitionError(
                f"Admin override: transition from 'arquivado' to '{to_status}' is not supported."
            )
    else:
        allowed = ALLOWED_TRANSITIONS.get(from_status, [])
        if to_status not in allowed:
            raise TransitionError(
                f"Transition from '{from_status}' to '{to_status}' is not allowed. "
                f"Allowed: {allowed}"
            )

    needs_justification = (from_status, to_status) in REQUIRES_JUSTIFICATION
    if needs_justification and not justification:
        raise JustificationRequired(
            f"Transition from '{from_status}' to '{to_status}' requires a written justification."
        )

    return TransitionResult(
        from_status=from_status,
        to_status=to_status,
        requires_justification=needs_justification,
        sets_closed_at=to_status in SETS_CLOSED_AT,
        sets_archived_at=to_status in SETS_ARCHIVED_AT,
        clears_closed_at=(from_status, to_status) in CLEARS_CLOSED_AT,
    )

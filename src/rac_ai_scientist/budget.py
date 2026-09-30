from __future__ import annotations

from .schemas import Budget, Usage


class LifecycleBudgetExhausted(RuntimeError):
    """Raised before a provider call when a known lifecycle limit is exhausted."""


def budget_exhaustion_reason(
    limit: Budget,
    observed: Usage,
    *,
    elapsed_seconds: float,
    provider_cost_known: bool,
) -> str | None:
    """Return the first exhausted provider-facing limit, if any.

    A request already in flight may make the observed totals exceed a ceiling.
    This guard prevents a subsequent request once that overage is known.  Cost
    is enforced only when the provider has supplied meaningful cost data.
    """

    checks = (
        (observed.agent_calls >= limit.agent_calls, "agent-call"),
        (observed.input_tokens >= limit.input_tokens, "input-token"),
        (observed.output_tokens >= limit.output_tokens, "output-token"),
        (elapsed_seconds >= limit.wall_seconds, "wall-time"),
        (
            provider_cost_known
            and observed.provider_cost_usd >= limit.provider_cost_usd,
            "provider-cost",
        ),
    )
    for exhausted, name in checks:
        if exhausted:
            return f"lifecycle {name} budget exhausted"
    return None


def require_provider_budget(
    limit: Budget,
    observed: Usage,
    *,
    elapsed_seconds: float,
    provider_cost_known: bool,
) -> None:
    reason = budget_exhaustion_reason(
        limit,
        observed,
        elapsed_seconds=elapsed_seconds,
        provider_cost_known=provider_cost_known,
    )
    if reason is not None:
        raise LifecycleBudgetExhausted(reason)

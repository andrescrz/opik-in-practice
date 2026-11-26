"""Per-model comparison table built from the routed calls."""

import statistics
from collections import defaultdict

from router_app.router import Call, short_name


def comparison_table(calls: list[Call]) -> str:
    by_model: dict[str, list[Call]] = defaultdict(list)
    for c in calls:
        by_model[c.model].append(c)

    lines = [
        f"{'Model':<30} {'Reviews':>7} {'Tokens':>7} {'Cost (USD)':>11} {'Mean latency':>13}",
        "-" * 72,
    ]
    for model, group in by_model.items():
        lines.append(
            f"{short_name(model):<30} {len(group):>7} {sum(c.tokens for c in group):>7} "
            f"{sum(c.cost_usd for c in group):>11.6f} {statistics.mean(c.latency_s for c in group):>12.2f}s"
        )
    return "\n".join(lines)

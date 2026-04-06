from __future__ import annotations

from collections import Counter

from .labels import SEVERITY_RANK


def build_prior_summary(session_records: list[dict]) -> str:
    if not session_records:
        return "previous_high_crisis: no; prior_subtypes: none; repeated_emergencies: 0; last_session_days_ago: unknown"

    severities = [record.get("final_severity", "low") for record in session_records]
    subtypes = [record.get("subtype", "general_distress") for record in session_records]
    emergency_count = sum(bool(record.get("emergency_flag")) for record in session_records)
    high_crisis = any(level == "high_crisis" for level in severities)
    latest_days = min(
        (record["days_ago"] for record in session_records if record.get("days_ago") is not None),
        default="unknown",
    )
    top_subtypes = Counter(subtypes).most_common(3)
    subtype_summary = ", ".join(label for label, _ in top_subtypes) if top_subtypes else "none"
    worst_severity = max(severities, key=lambda item: SEVERITY_RANK.get(item, 0))

    return (
        f"previous_high_crisis: {'yes' if high_crisis else 'no'}; "
        f"worst_previous_severity: {worst_severity}; "
        f"prior_subtypes: {subtype_summary}; "
        f"repeated_emergencies: {emergency_count}; "
        f"last_session_days_ago: {latest_days}"
    )

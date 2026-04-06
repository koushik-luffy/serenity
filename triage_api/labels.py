from __future__ import annotations

SEVERITY_LABELS = ["low", "medium", "high_crisis"]
SUBTYPE_LABELS = [
    "suicidal_ideation",
    "self_harm",
    "panic_anxiety",
    "depression_hopelessness",
    "abuse_violence",
    "substance_overdose",
    "accident_injury",
    "general_distress",
]

SEVERITY_RANK = {label: index for index, label in enumerate(SEVERITY_LABELS)}
INDEX_TO_SEVERITY = {index: label for index, label in enumerate(SEVERITY_LABELS)}
SUBTYPE_TO_INDEX = {label: index for index, label in enumerate(SUBTYPE_LABELS)}
INDEX_TO_SUBTYPE = {index: label for index, label in enumerate(SUBTYPE_LABELS)}

SEVERITY_BASE_RISK = {
    "low": 20,
    "medium": 55,
    "high_crisis": 82,
}

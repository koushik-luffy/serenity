from __future__ import annotations

import re
from dataclasses import dataclass

from .labels import SEVERITY_BASE_RISK, SEVERITY_LABELS, SEVERITY_RANK


@dataclass
class RuleSignal:
    label: str
    severity_floor: str | None = None
    subtype_hint: str | None = None
    emergency_flag: bool = False
    risk_boost: int = 0


@dataclass
class RuleAssessment:
    severity_floor: str | None
    subtype_hint: str | None
    emergency_flag: bool
    indicators: list[str]
    risk_boost: int


HIGH_CRISIS_RULES: list[tuple[re.Pattern[str], RuleSignal]] = [
    (
        re.compile(r"\b(kill myself|end my life|suicide plan|want to die|don't want to live|take my own life)\b", re.I),
        RuleSignal("explicit suicidal intent", "high_crisis", "suicidal_ideation", False, 26),
    ),
    (
        re.compile(
            r"\b(better off without me|wish i could disappear|if i didn't wake up|if i don't wake up|running out of reasons to stay|don't see the point in waking up|want everything to stop forever)\b",
            re.I,
        ),
        RuleSignal("indirect suicidal ideation", "high_crisis", "suicidal_ideation", False, 22),
    ),
    (
        re.compile(r"\b(cut myself|hurt myself|self harm|bleeding myself)\b", re.I),
        RuleSignal("self-harm language", "high_crisis", "self_harm", False, 22),
    ),
    (
        re.compile(r"\b(overdose|too many pills|poisoned myself)\b", re.I),
        RuleSignal("overdose language", "high_crisis", "substance_overdose", True, 28),
    ),
    (
        re.compile(r"\b(he hit me|she hit me|being abused|domestic violence|someone is attacking me)\b", re.I),
        RuleSignal("violence or abuse danger", "high_crisis", "abuse_violence", True, 24),
    ),
    (
        re.compile(
            r"\b(kill him|kill her|kill them|kill someone|hurt someone|hurt him|hurt her|hurt them|kidnap someone|kidnap him|kidnap her|make them disappear)\b",
            re.I,
        ),
        RuleSignal("threats of harm to others", "high_crisis", "abuse_violence", True, 28),
    ),
    (
        re.compile(
            r"\b(make him disappear|make her disappear|make someone disappear|might snap and hurt him|might snap and hurt her|might snap and hurt them|lose control and hurt someone|can't trust myself around him|can't trust myself around her|can't trust myself around them|visions of hurting him|visions of hurting her|visions of hurting them)\b",
            re.I,
        ),
        RuleSignal("indirect threats of harm to others", "high_crisis", "abuse_violence", True, 24),
    ),
    (
        re.compile(r"\b(car crash|accident|broken bone|can't breathe|collapsed|unconscious)\b", re.I),
        RuleSignal("physical emergency language", "high_crisis", "accident_injury", True, 30),
    ),
]

MEDIUM_RULES: list[tuple[re.Pattern[str], RuleSignal]] = [
    (
        re.compile(r"\b(panic attack|can't calm down|heart racing|hyperventilat)\w*", re.I),
        RuleSignal("panic symptoms", "medium", "panic_anxiety", False, 14),
    ),
    (
        re.compile(r"\b(hopeless|empty|worthless|numb|nothing matters)\b", re.I),
        RuleSignal("hopelessness language", "medium", "depression_hopelessness", False, 12),
    ),
    (
        re.compile(r"\b(overwhelmed|breaking down|can't handle this|falling apart)\b", re.I),
        RuleSignal("acute distress language", "medium", "general_distress", False, 10),
    ),
]

LOW_RULES: list[tuple[re.Pattern[str], RuleSignal]] = [
    (
        re.compile(r"\b(stressed|anxious|worried|sad|can't sleep)\b", re.I),
        RuleSignal("stress or sadness language", "low", "general_distress", False, 4),
    ),
]

HISTORY_RULES: list[tuple[re.Pattern[str], RuleSignal]] = [
    (
        re.compile(r"previous_high_crisis:\s*yes", re.I),
        RuleSignal("prior high-crisis history", "medium", None, False, 8),
    ),
    (
        re.compile(r"prior_subtypes:\s*.*suicidal_ideation", re.I),
        RuleSignal("prior suicidal ideation history", "medium", "suicidal_ideation", False, 10),
    ),
    (
        re.compile(r"repeated_emergencies:\s*([1-9]\d*)", re.I),
        RuleSignal("repeated emergency history", "medium", None, True, 10),
    ),
]


def _choose_more_severe(first: str | None, second: str | None) -> str | None:
    if first is None:
        return second
    if second is None:
        return first
    return first if SEVERITY_RANK[first] >= SEVERITY_RANK[second] else second


def assess_rules(messages: list[str], prior_summary: str | None = None) -> RuleAssessment:
    severity_floor: str | None = None
    subtype_hint: str | None = None
    emergency_flag = False
    indicators: list[str] = []
    risk_boost = 0

    text = "\n".join(messages)
    for rules in (HIGH_CRISIS_RULES, MEDIUM_RULES, LOW_RULES):
        for pattern, signal in rules:
            if pattern.search(text):
                severity_floor = _choose_more_severe(severity_floor, signal.severity_floor)
                subtype_hint = subtype_hint or signal.subtype_hint
                emergency_flag = emergency_flag or signal.emergency_flag
                risk_boost += signal.risk_boost
                indicators.append(signal.label)

    if prior_summary:
        for pattern, signal in HISTORY_RULES:
            if pattern.search(prior_summary):
                severity_floor = _choose_more_severe(severity_floor, signal.severity_floor)
                subtype_hint = subtype_hint or signal.subtype_hint
                emergency_flag = emergency_flag or signal.emergency_flag
                risk_boost += signal.risk_boost
                indicators.append(signal.label)

    return RuleAssessment(
        severity_floor=severity_floor,
        subtype_hint=subtype_hint,
        emergency_flag=emergency_flag,
        indicators=indicators[:4],
        risk_boost=risk_boost,
    )


def apply_safe_fail(
    severity: str,
    subtype: str,
    emergency_flag: bool,
    confidence: float,
    rule_assessment: RuleAssessment,
) -> tuple[str, str, bool, bool]:
    final_severity = severity
    final_subtype = subtype
    final_emergency = emergency_flag or rule_assessment.emergency_flag
    escalated = False

    if rule_assessment.severity_floor and SEVERITY_RANK[final_severity] < SEVERITY_RANK[rule_assessment.severity_floor]:
        final_severity = rule_assessment.severity_floor
        escalated = True

    if confidence < 0.45 and final_severity != "high_crisis":
        final_severity = SEVERITY_LABELS[min(SEVERITY_RANK[final_severity] + 1, len(SEVERITY_LABELS) - 1)]
        escalated = True

    if rule_assessment.subtype_hint and (
        final_subtype == "general_distress"
        or (
            rule_assessment.severity_floor == "high_crisis"
            and final_subtype != rule_assessment.subtype_hint
        )
    ):
        final_subtype = rule_assessment.subtype_hint
        escalated = True

    return final_severity, final_subtype, final_emergency, escalated


def compute_risk_score(
    severity: str,
    emergency_flag: bool,
    confidence: float,
    subtype: str,
    rule_assessment: RuleAssessment,
) -> float:
    score = SEVERITY_BASE_RISK[severity]
    score += rule_assessment.risk_boost
    score += 12 if emergency_flag else 0
    score += 6 if subtype in {"suicidal_ideation", "self_harm", "substance_overdose", "accident_injury", "abuse_violence"} else 0
    score += int((1 - confidence) * 10)
    return max(0.0, min(100.0, float(score)))

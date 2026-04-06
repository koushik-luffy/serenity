from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import torch

from .history import build_prior_summary
from .labels import INDEX_TO_SEVERITY, INDEX_TO_SUBTYPE, SEVERITY_RANK
from .model import HierarchicalTriageModel
from .rules import apply_safe_fail, assess_rules, compute_risk_score

try:
    from transformers import AutoTokenizer
except ImportError:  # pragma: no cover
    AutoTokenizer = None


MAX_RECENT_MESSAGES = 8


@dataclass
class Prediction:
    severity: str
    subtype: str
    emergency_flag: bool
    confidence: float
    risk_score: float


class InferenceBackend(Protocol):
    def predict(self, recent_messages: list[str], prior_summary: str | None) -> Prediction:
        ...


class HeuristicFallbackBackend:
    def predict(self, recent_messages: list[str], prior_summary: str | None) -> Prediction:
        combined = " ".join(recent_messages).lower()
        severity = "low"
        subtype = "general_distress"
        confidence = 0.58
        emergency = False

        if any(term in combined for term in ["panic", "heart racing", "hyperventilating", "anxiety"]):
            severity = "medium"
            subtype = "panic_anxiety"
            confidence = 0.67
        if any(term in combined for term in ["hopeless", "worthless", "empty", "nothing matters"]):
            severity = "medium"
            subtype = "depression_hopelessness"
            confidence = max(confidence, 0.69)
        if any(term in combined for term in ["kill myself", "want to die", "suicide", "end my life"]):
            severity = "high_crisis"
            subtype = "suicidal_ideation"
            confidence = 0.9
        if any(term in combined for term in ["cut myself", "self harm", "hurt myself"]):
            severity = "high_crisis"
            subtype = "self_harm"
            confidence = 0.88
        if any(term in combined for term in ["overdose", "too many pills"]):
            severity = "high_crisis"
            subtype = "substance_overdose"
            confidence = 0.9
            emergency = True
        if any(term in combined for term in ["car crash", "accident", "collapsed", "can't breathe"]):
            severity = "high_crisis"
            subtype = "accident_injury"
            confidence = 0.92
            emergency = True
        if prior_summary and "previous_high_crisis: yes" in prior_summary.lower():
            severity = severity if SEVERITY_RANK[severity] >= SEVERITY_RANK["medium"] else "medium"
            confidence = max(confidence, 0.62)

        risk_score = 90.0 if severity == "high_crisis" else 58.0 if severity == "medium" else 24.0
        if emergency:
            risk_score = min(100.0, risk_score + 8.0)

        return Prediction(severity, subtype, emergency, confidence, risk_score)


class TransformerBackend:
    def __init__(self, encoder_name: str, weights_path: str) -> None:
        if AutoTokenizer is None:
            raise RuntimeError("transformers is not installed")
        self.tokenizer = AutoTokenizer.from_pretrained(encoder_name)
        self.model = HierarchicalTriageModel(encoder_name=encoder_name)
        state = torch.load(weights_path, map_location="cpu")
        self.model.load_state_dict(state)
        self.model.eval()

    def _tokenize_turns(self, turns: list[str]) -> tuple[torch.Tensor, torch.Tensor]:
        texts = turns[:MAX_RECENT_MESSAGES]
        if len(texts) < MAX_RECENT_MESSAGES:
            texts = texts + [""] * (MAX_RECENT_MESSAGES - len(texts))
        encoded = self.tokenizer(
            texts,
            padding="max_length",
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        return encoded["input_ids"].unsqueeze(0), encoded["attention_mask"].unsqueeze(0)

    def _tokenize_summary(self, summary: str | None) -> tuple[torch.Tensor, torch.Tensor]:
        encoded = self.tokenizer(
            summary or "previous_high_crisis: no; prior_subtypes: none; repeated_emergencies: 0",
            padding="max_length",
            truncation=True,
            max_length=96,
            return_tensors="pt",
        )
        return encoded["input_ids"], encoded["attention_mask"]

    def predict(self, recent_messages: list[str], prior_summary: str | None) -> Prediction:
        turn_ids, turn_mask = self._tokenize_turns(recent_messages)
        history_ids, history_mask = self._tokenize_summary(prior_summary)
        with torch.no_grad():
            outputs = self.model(
                turn_input_ids=turn_ids,
                turn_attention_mask=turn_mask,
                history_input_ids=history_ids,
                history_attention_mask=history_mask,
            )
            severity_probs = torch.softmax(outputs.severity_logits, dim=-1)
            subtype_probs = torch.softmax(outputs.subtype_logits, dim=-1)
            emergency_probs = torch.sigmoid(outputs.emergency_logits)
            severity_idx = int(severity_probs.argmax(dim=-1).item())
            subtype_idx = int(subtype_probs.argmax(dim=-1).item())
            confidence = float(max(severity_probs[0, severity_idx].item(), subtype_probs[0, subtype_idx].item()))
            return Prediction(
                severity=INDEX_TO_SEVERITY[severity_idx],
                subtype=INDEX_TO_SUBTYPE[subtype_idx],
                emergency_flag=bool(emergency_probs.item() >= 0.5),
                confidence=confidence,
                risk_score=float(outputs.risk_score.item()),
            )


def _format_recent_messages(messages: list[dict]) -> list[str]:
    sliced = messages[-MAX_RECENT_MESSAGES:]
    return [f"[{message['role'].upper()}] {message['content'].strip()}" for message in sliced]


class TriageService:
    def __init__(self) -> None:
        encoder_name = os.getenv("TRIAGE_ENCODER_NAME", "microsoft/deberta-v3-base")
        weights_path = os.getenv("TRIAGE_MODEL_WEIGHTS", "")
        self.backend: InferenceBackend
        if weights_path and os.path.exists(weights_path):
            self.backend = TransformerBackend(encoder_name, weights_path)
        else:
            self.backend = HeuristicFallbackBackend()

    def summarize_history(self, session_records: list[dict]) -> str:
        return build_prior_summary(session_records)

    def analyze(self, session_id: str, recent_messages: list[dict], prior_summary: str | None) -> dict:
        formatted_messages = _format_recent_messages(recent_messages)
        rule_assessment = assess_rules(formatted_messages, prior_summary)
        neural = self.backend.predict(formatted_messages, prior_summary)

        final_severity, final_subtype, final_emergency, escalated = apply_safe_fail(
            severity=neural.severity,
            subtype=neural.subtype,
            emergency_flag=neural.emergency_flag,
            confidence=neural.confidence,
            rule_assessment=rule_assessment,
        )

        final_confidence = neural.confidence if not escalated else max(0.5, neural.confidence)
        final_risk = compute_risk_score(
            severity=final_severity,
            emergency_flag=final_emergency,
            confidence=final_confidence,
            subtype=final_subtype,
            rule_assessment=rule_assessment,
        )

        return {
            "session_id": session_id,
            "severity": final_severity,
            "subtype": final_subtype,
            "emergency_flag": final_emergency,
            "risk_score": final_risk,
            "confidence": final_confidence,
            "top_indicators": rule_assessment.indicators,
            "safe_fail_escalated": escalated,
            "neural_prediction": {
                "severity": neural.severity,
                "subtype": neural.subtype,
                "emergency_flag": neural.emergency_flag,
                "risk_score": max(0.0, min(100.0, float(neural.risk_score))),
                "confidence": neural.confidence,
            },
            "final_prediction": {
                "severity": final_severity,
                "subtype": final_subtype,
                "emergency_flag": final_emergency,
                "risk_score": final_risk,
                "confidence": final_confidence,
            },
        }

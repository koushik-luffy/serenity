from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TriageStore:
    def __init__(self) -> None:
        self.queue: dict[str, dict] = {}
        self.audit: list[dict] = []
        self.contacts: dict[str, list[dict]] = {}
        self.alerts: list[dict] = []

    def record_analysis(self, session_id: str, user_id: str, last_message: str, result: dict) -> None:
        timestamp = _utc_now()
        queue_entry = {
            "session_id": session_id,
            "user_id": user_id,
            "severity": result["severity"],
            "subtype": result["subtype"],
            "emergency_flag": result["emergency_flag"],
            "risk_score": result["risk_score"],
            "confidence": result["confidence"],
            "last_message": last_message,
            "top_indicators": result.get("top_indicators", []),
            "status": "active",
            "timestamp": timestamp,
        }
        self.queue[session_id] = queue_entry
        self.audit.append(
            {
                "session_id": session_id,
                "user_id": user_id,
                "severity": result["severity"],
                "subtype": result["subtype"],
                "message": last_message,
                "timestamp": timestamp,
                "event": "analysis",
                "emergency_flag": result["emergency_flag"],
                "risk_score": result["risk_score"],
            }
        )

    def get_queue_item(self, session_id: str) -> dict | None:
        item = self.queue.get(session_id)
        return deepcopy(item) if item else None

    def replace_contacts(self, user_id: str, contacts: list[dict]) -> list[dict]:
        timestamp = _utc_now()
        records: list[dict] = []
        for contact in contacts:
            records.append(
                {
                    "contact_id": uuid4().hex,
                    "name": contact["name"],
                    "relationship": contact["relationship"],
                    "phone_number": contact.get("phone_number"),
                    "email": contact.get("email"),
                    "preferred_channel": contact["preferred_channel"],
                    "is_primary": contact.get("is_primary", False),
                    "notes": contact.get("notes"),
                    "created_at": timestamp,
                }
            )

        self.contacts[user_id] = records
        self.audit.append(
            {
                "user_id": user_id,
                "severity": "low",
                "subtype": "general_distress",
                "message": f"[CONTACTS] Stored {len(records)} emergency contacts",
                "timestamp": timestamp,
                "event": "emergency_contacts_updated",
                "emergency_flag": False,
                "risk_score": 0,
            }
        )
        return deepcopy(records)

    def get_contacts(self, user_id: str) -> list[dict]:
        return deepcopy(self.contacts.get(user_id, []))

    def record_alert(
        self,
        *,
        user_id: str,
        session_id: str,
        severity: str,
        risk_score: float,
        last_message: str,
        status: str,
        deliveries: list[dict],
    ) -> dict:
        alert = {
            "alert_id": uuid4().hex,
            "user_id": user_id,
            "session_id": session_id,
            "severity": severity,
            "risk_score": risk_score,
            "status": status,
            "last_message": last_message,
            "deliveries": deepcopy(deliveries),
            "timestamp": _utc_now(),
        }
        self.alerts.append(alert)
        self.audit.append(
            {
                "user_id": user_id,
                "severity": severity,
                "subtype": self.queue.get(session_id, {}).get("subtype", "general_distress"),
                "message": f"[ALERT] {status}",
                "timestamp": alert["timestamp"],
                "event": "emergency_alert",
                "emergency_flag": True,
                "risk_score": risk_score,
            }
        )
        return deepcopy(alert)

    def get_alerts(self) -> list[dict]:
        return deepcopy(self.alerts[-200:])

    def update_status(self, session_id: str, status: str, message: str | None = None) -> dict | None:
        updated_item: dict | None = None
        if session_id in self.queue:
            self.queue[session_id]["status"] = status
            self.queue[session_id]["timestamp"] = _utc_now()
            if message:
                self.queue[session_id]["last_message"] = message
            updated_item = deepcopy(self.queue[session_id])
        self.audit.append(
            {
                "session_id": session_id,
                "user_id": self.queue.get(session_id, {}).get("user_id", session_id),
                "severity": self.queue.get(session_id, {}).get("severity", "low"),
                "subtype": self.queue.get(session_id, {}).get("subtype", "general_distress"),
                "message": message or f"[STATUS] {status}",
                "timestamp": _utc_now(),
                "event": status,
                "emergency_flag": self.queue.get(session_id, {}).get("emergency_flag", False),
                "risk_score": self.queue.get(session_id, {}).get("risk_score", 0),
            }
        )
        return updated_item

    def get_queue(self) -> list[dict]:
        items = list(self.queue.values())
        items.sort(key=lambda item: (-item["risk_score"], item["timestamp"]), reverse=False)
        return deepcopy(items)

    def get_audit(self) -> list[dict]:
        return deepcopy(self.audit[-200:])

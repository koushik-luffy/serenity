from __future__ import annotations

from copy import deepcopy


ALERT_THRESHOLD_LABEL = "high_crisis + emergency_flag or risk_score>=90"


class EmergencyAlertService:
    def __init__(self, store) -> None:
        self.store = store

    def should_alert(self, result: dict) -> bool:
        return result["severity"] == "high_crisis" and (
            result["emergency_flag"] or result["risk_score"] >= 90.0
        )

    def trigger_if_needed(
        self,
        *,
        user_id: str,
        session_id: str,
        last_message: str,
        result: dict,
    ) -> dict:
        if not self.should_alert(result):
            return {
                "triggered": False,
                "alert_id": None,
                "user_id": user_id,
                "session_id": session_id,
                "threshold": ALERT_THRESHOLD_LABEL,
                "status": "not_triggered",
                "deliveries": [],
            }

        contacts = self.store.get_contacts(user_id)
        if not contacts:
            alert_record = self.store.record_alert(
                user_id=user_id,
                session_id=session_id,
                severity=result["severity"],
                risk_score=result["risk_score"],
                last_message=last_message,
                status="no_contacts",
                deliveries=[],
            )
            return {
                "triggered": True,
                "alert_id": alert_record["alert_id"],
                "user_id": user_id,
                "session_id": session_id,
                "threshold": ALERT_THRESHOLD_LABEL,
                "status": "no_contacts",
                "deliveries": [],
            }

        deliveries: list[dict] = []
        for contact in contacts:
            preferred_channel = contact["preferred_channel"]
            if preferred_channel == "sms" and contact.get("phone_number"):
                target = contact["phone_number"]
                status = "simulated"
                reason = "Queued for future SMS integration."
            elif preferred_channel == "email" and contact.get("email"):
                target = contact["email"]
                status = "simulated"
                reason = "Queued for future email integration."
            else:
                fallback_target = contact.get("phone_number") or contact.get("email")
                target = fallback_target or "missing-contact-method"
                status = "skipped"
                reason = "Preferred delivery channel is unavailable for this contact."

            deliveries.append(
                {
                    "contact_id": contact["contact_id"],
                    "contact_name": contact["name"],
                    "channel": preferred_channel,
                    "target": target,
                    "status": status,
                    "reason": reason,
                }
            )

        alert_record = self.store.record_alert(
            user_id=user_id,
            session_id=session_id,
            severity=result["severity"],
            risk_score=result["risk_score"],
            last_message=last_message,
            status="simulated",
            deliveries=deliveries,
        )
        response = deepcopy(alert_record)
        response["triggered"] = True
        response["threshold"] = ALERT_THRESHOLD_LABEL
        return response

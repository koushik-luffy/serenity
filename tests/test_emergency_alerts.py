import unittest

from fastapi.testclient import TestClient

from triage_api.main import create_app


class EmergencyAlertApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_can_store_and_fetch_emergency_contacts(self) -> None:
        response = self.client.post(
            "/api/emergency-contacts",
            json={
                "user_id": "user-123",
                "contacts": [
                    {
                        "name": "Aisha Khan",
                        "relationship": "sister",
                        "phone_number": "+911234567890",
                        "preferred_channel": "sms",
                        "is_primary": True,
                    },
                    {
                        "name": "Rahul Mehta",
                        "relationship": "friend",
                        "email": "rahul@example.com",
                        "preferred_channel": "email",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user_id"], "user-123")
        self.assertEqual(len(body["contacts"]), 2)

        fetch_response = self.client.get("/api/emergency-contacts/user-123")
        self.assertEqual(fetch_response.status_code, 200)
        fetch_body = fetch_response.json()
        self.assertEqual(len(fetch_body["contacts"]), 2)
        self.assertEqual(fetch_body["contacts"][0]["name"], "Aisha Khan")

    def test_high_crisis_analysis_triggers_simulated_alerts(self) -> None:
        self.client.post(
            "/api/emergency-contacts",
            json={
                "user_id": "user-999",
                "contacts": [
                    {
                        "name": "Emergency Contact",
                        "relationship": "parent",
                        "phone_number": "+911111111111",
                        "preferred_channel": "sms",
                        "is_primary": True,
                    }
                ],
            },
        )

        response = self.client.post(
            "/triage/analyze",
            json={
                "session_id": "session-999",
                "user_id": "user-999",
                "recent_messages": [
                    {"role": "user", "content": "My friend collapsed after a car crash and can't breathe."}
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["severity"], "high_crisis")
        self.assertTrue(body["emergency_flag"])
        self.assertTrue(body["emergency_alert"]["triggered"])
        self.assertEqual(body["emergency_alert"]["status"], "simulated")
        self.assertEqual(len(body["emergency_alert"]["deliveries"]), 1)
        self.assertEqual(body["emergency_alert"]["deliveries"][0]["status"], "simulated")

        alerts_response = self.client.get("/api/alerts")
        self.assertEqual(alerts_response.status_code, 200)
        alerts_body = alerts_response.json()
        self.assertEqual(len(alerts_body["alerts"]), 1)
        self.assertEqual(alerts_body["alerts"][0]["user_id"], "user-999")

    def test_high_crisis_without_contacts_records_gap(self) -> None:
        response = self.client.post(
            "/triage/analyze",
            json={
                "session_id": "session-no-contact",
                "user_id": "user-no-contact",
                "recent_messages": [
                    {"role": "user", "content": "I overdosed on too many pills."}
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["emergency_alert"]["triggered"])
        self.assertEqual(body["emergency_alert"]["status"], "no_contacts")

    def test_counselor_can_take_queue_actions(self) -> None:
        analyze_response = self.client.post(
            "/triage/analyze",
            json={
                "session_id": "session-action",
                "user_id": "user-action",
                "recent_messages": [
                    {"role": "user", "content": "I am panicking and I cannot calm down."}
                ],
            },
        )
        self.assertEqual(analyze_response.status_code, 200)

        action_response = self.client.post(
            "/api/queue/session-action/actions",
            json={"action": "start_outreach"},
        )
        self.assertEqual(action_response.status_code, 200)
        body = action_response.json()
        self.assertEqual(body["action"], "start_outreach")
        self.assertEqual(body["queue_item"]["status"], "outreach_started")

        queue_response = self.client.get("/api/queue")
        self.assertEqual(queue_response.status_code, 200)
        queue_body = queue_response.json()
        self.assertEqual(queue_body["queue"][0]["session_id"], "session-action")
        self.assertEqual(queue_body["queue"][0]["user_id"], "user-action")


if __name__ == "__main__":
    unittest.main()

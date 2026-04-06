import unittest

from triage_api.history import build_prior_summary


class HistorySummaryTests(unittest.TestCase):
    def test_builds_compact_summary(self) -> None:
        summary = build_prior_summary(
            [
                {
                    "session_id": "abc",
                    "final_severity": "high_crisis",
                    "subtype": "panic_anxiety",
                    "emergency_flag": True,
                    "days_ago": 3,
                },
                {
                    "session_id": "def",
                    "final_severity": "medium",
                    "subtype": "panic_anxiety",
                    "emergency_flag": False,
                    "days_ago": 10,
                },
            ]
        )
        self.assertIn("previous_high_crisis: yes", summary)
        self.assertIn("prior_subtypes: panic_anxiety", summary)
        self.assertIn("repeated_emergencies: 1", summary)


if __name__ == "__main__":
    unittest.main()

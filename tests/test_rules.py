import unittest

from triage_api.rules import apply_safe_fail, assess_rules


class RuleTests(unittest.TestCase):
    def test_explicit_suicide_language_forces_high_crisis(self) -> None:
        assessment = assess_rules(["[USER] I want to kill myself tonight"], None)
        severity, subtype, emergency, escalated = apply_safe_fail(
            severity="low",
            subtype="general_distress",
            emergency_flag=False,
            confidence=0.91,
            rule_assessment=assessment,
        )
        self.assertEqual(severity, "high_crisis")
        self.assertEqual(subtype, "suicidal_ideation")
        self.assertFalse(emergency)
        self.assertTrue(escalated)

    def test_panic_distress_stays_medium(self) -> None:
        assessment = assess_rules(["[USER] I am having a panic attack and my heart is racing"], None)
        severity, subtype, emergency, escalated = apply_safe_fail(
            severity="medium",
            subtype="panic_anxiety",
            emergency_flag=False,
            confidence=0.8,
            rule_assessment=assessment,
        )
        self.assertEqual(severity, "medium")
        self.assertEqual(subtype, "panic_anxiety")
        self.assertFalse(emergency)
        self.assertFalse(escalated)

    def test_accident_flags_emergency(self) -> None:
        assessment = assess_rules(["[USER] My friend collapsed after a car crash"], None)
        severity, subtype, emergency, escalated = apply_safe_fail(
            severity="medium",
            subtype="general_distress",
            emergency_flag=False,
            confidence=0.51,
            rule_assessment=assessment,
        )
        self.assertEqual(severity, "high_crisis")
        self.assertEqual(subtype, "accident_injury")
        self.assertTrue(emergency)
        self.assertTrue(escalated)

    def test_low_confidence_escalates_upward(self) -> None:
        assessment = assess_rules(["[USER] I cannot do this anymore"], None)
        severity, subtype, emergency, escalated = apply_safe_fail(
            severity="low",
            subtype="general_distress",
            emergency_flag=False,
            confidence=0.22,
            rule_assessment=assessment,
        )
        self.assertEqual(severity, "medium")
        self.assertTrue(escalated)


if __name__ == "__main__":
    unittest.main()

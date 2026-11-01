import json
import unittest

import app


class EvidenceChecks(unittest.TestCase):
    def setUp(self):
        self.answer = "I hear the claimant."
        self.rows = [{"score": 1, "quote": "hear the claimant", "feedback": "Specify a time."}
                     for _ in range(3)]

    def test_valid(self):
        self.assertEqual(app.validate(self.rows, self.answer), self.rows)

    def test_reject_fabricated_evidence(self):
        self.rows[0]["quote"] = "I allow the appeal"
        with self.assertRaises(ValueError):
            app.validate(self.rows, self.answer)

    def test_abstain_when_incomplete(self):
        with self.assertRaises(ValueError):
            app.validate(self.rows[:2], self.answer)

    def test_reject_empty_or_boolean_positive(self):
        for rating in ({"score": 2, "quote": ""}, {"score": True, "quote": "I"}):
            self.rows[0].update(rating)
            with self.assertRaises(ValueError):
                app.validate(self.rows, self.answer)

    def test_bank(self):
        bank = json.loads((app.ROOT / "bank.json").read_text())
        self.assertGreaterEqual(len(bank), 18)
        self.assertEqual(len({i["id"] for i in bank}), len(bank))
        for i in bank:
            self.assertTrue(all(i.get(k) for k in ("id", "domain", "title", "prompt")))
            self.assertEqual(len(i["criteria"]), 3)


if __name__ == "__main__":
    unittest.main()

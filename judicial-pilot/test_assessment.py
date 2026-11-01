"""Offline checks. The reviewer transport is mocked and records use a temporary directory."""
import base64
import io
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from forms import AssessmentBank
import frontier
from records import Archive


ROOT = Path(__file__).resolve().parent


class FormsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = AssessmentBank(ROOT)

    def test_total_distinct_questions_and_meaningful_components(self):
        catalogue = self.bank.catalogue()
        self.assertEqual(catalogue["total"], 4000)
        self.assertEqual([entry["count"] for entry in catalogue["categories"]], [200] * 20)
        questions = [self.bank.question(i) for i in range(catalogue["total"])]
        self.assertEqual(len({q["id"] for q in questions}), 4000)
        self.assertEqual(len({(q["record"], q["development"], q["task"]) for q in questions}), 4000)

    def test_each_form_has_one_per_category_and_replays_in_order(self):
        for _ in range(10):
            form = self.bank.new_form()
            self.assertEqual(len(form["questions"]), 20)
            self.assertEqual({q["id"][:3] for q in form["questions"]}, {f"C{i:02d}" for i in range(1, 21)})
            self.assertEqual(self.bank.replay(form["id"]), form)

    def test_replay_rejects_wrong_version_truncation_and_unbalanced_form(self):
        current = self.bank.new_form()["id"]
        unbalanced = base64.urlsafe_b64encode(struct.pack(">20H", *([0] * 20))).decode().rstrip("=")
        for bad in (current[:-1], current.replace("v1-", "v99-", 1), self.bank.version + "." + unbalanced):
            with self.subTest(form=bad), self.assertRaises(ValueError):
                self.bank.replay(bad)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.archive = Archive(self.directory)
        self.addCleanup(self.archive.file_lock.close)
        self.bank = AssessmentBank(ROOT)
        self.form = self.bank.new_form()
        self.attempt = str(uuid4())
        self.answers = {q["id"]: f"Fictional response for {q['id']}." for q in self.form["questions"]}

    def save(self):
        return self.archive.save(self.attempt, self.form, self.answers, self.bank)

    def test_repeated_save_conflict_and_reopen(self):
        self.assertEqual(self.save(), self.attempt)
        self.assertEqual(self.save(), self.attempt)
        self.assertEqual(len(self.archive.list()["submissions"]), 1)
        expected = self.archive.get(self.attempt)
        self.answers[self.form["questions"][0]["id"]] += " Changed."
        with self.assertRaises(FileExistsError):
            self.save()
        self.assertEqual(self.archive.get(self.attempt), expected)
        self.archive.file_lock.close()
        reopened = Archive(self.directory)
        self.addCleanup(reopened.file_lock.close)
        self.assertEqual(reopened.get(self.attempt), expected)
        self.assertEqual([i["question"] for i in expected["items"]], self.form["questions"])

    def test_batch_failure_stops_reviewer_and_retry_preserves_completed_items(self):
        self.save()
        first_id = self.form["questions"][0]["id"]
        self.assertEqual(self.archive.enqueue(self.attempt), 20)
        self.assertTrue(self.archive.run_one(lambda item: {"id": item["question"]["id"], "pass": 1}))

        def unavailable(_):
            raise RuntimeError("Synthetic outage")

        self.assertTrue(self.archive.run_one(unavailable))
        self.assertFalse(self.archive.run_one(unavailable))
        counts = self.archive.list()["submissions"][0]["counts"]
        self.assertEqual((counts["complete"], counts["failed"], counts["queued"]), (1, 19, 0))
        self.assertEqual(self.archive.enqueue(self.attempt), 19)
        retried = []

        def successful(item):
            retried.append(item["question"]["id"])
            return {"pass": 2}

        while self.archive.run_one(successful):
            pass
        self.assertEqual(retried, [q["id"] for q in self.form["questions"][1:]])
        stored = self.archive.get(self.attempt)["items"]
        self.assertEqual(stored[0]["review"], {"id": first_id, "pass": 1})
        self.assertTrue(all(i["state"] == "complete" for i in stored))
        self.assertEqual(self.archive.enqueue(self.attempt), 0)

    def test_interrupted_review_is_retained_for_explicit_retry(self):
        self.save()
        self.archive.enqueue(self.attempt)
        with self.archive.db() as db:
            db.execute("UPDATE items SET state='running' WHERE submission=? AND position=0", (self.attempt,))
        self.archive.file_lock.close()
        reopened = Archive(self.directory)
        self.addCleanup(reopened.file_lock.close)
        record = reopened.get(self.attempt)
        self.assertEqual(record["items"][0]["state"], "failed")
        self.assertIn("restarted", record["items"][0]["error"])
        self.assertIsNone(record["items"][0]["review"])
        self.assertTrue(all(i["state"] == "queued" for i in record["items"][1:]))
        self.assertEqual(record["items"][0]["answer"], self.answers[self.form["questions"][0]["id"]])


class FrontierTests(unittest.TestCase):
    def setUp(self):
        self.item = {"answer": "Hear the applicant today. Contact the registrar tomorrow.",
                     "question": {"title": "A fictional hearing"}, "criteria": ["A", "B", "C"]}
        self.rows = [{"criterion": 1, "score": 2, "evidence": [1], "conflict": 0, "feedback": "Specific hearing."},
                     {"criterion": 2, "score": 1, "evidence": [2], "conflict": 1, "feedback": "Explain timing."},
                     {"criterion": 3, "score": None, "evidence": [], "conflict": 0, "feedback": "Not elicited."}]

    def score(self, *, model=None, content=None):
        if content is None:
            content = [{"type": "output_text", "text": json.dumps({"ratings": self.rows})}]
        envelope = {"id": "resp_offline", "status": "completed", "model": model or frontier.MODEL,
                    "output": [{"type": "message", "content": content}]}
        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline_test_only"}), patch.object(
                frontier, "urlopen", return_value=io.BytesIO(json.dumps(envelope).encode())) as transport:
            result = frontier.review(self.item)
            request = json.loads(transport.call_args.args[0].data)
            self.assertEqual(request["model"], frontier.MODEL)
            self.assertFalse(request["store"])
            return result

    def test_valid_review_binds_to_actual_passages_and_preserves_abstention(self):
        result = self.score()
        self.assertEqual(result["ratings"][0]["quote"], "Hear the applicant today.")
        self.assertEqual(result["ratings"][1]["evidence"], ["Contact the registrar tomorrow."])
        self.assertEqual(result["ratings"][1]["conflict"], "Hear the applicant today.")
        self.assertIsNone(result["ratings"][2]["score"])
        self.assertEqual(result["responseId"], "resp_offline")

    def test_reject_other_model(self):
        with self.assertRaises(ValueError):
            self.score(model="different-model")

    def test_reject_out_of_range_reference_and_missing_positive_evidence(self):
        for refs in ([0], [3], []):
            self.rows[0]["evidence"] = refs
            with self.subTest(refs=refs), self.assertRaises(ValueError):
                self.score()

    def test_reject_refusal_and_absent_output(self):
        for parts in ([], [{"type": "refusal", "refusal": "No review."}]):
            with self.subTest(parts=parts), self.assertRaises(ValueError):
                self.score(content=parts)


class CredentialTests(unittest.TestCase):
    def test_only_explicit_openai_token_is_loaded(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True):
            path = Path(temp) / "key-fixture.md"
            token = "sk-" + "a" * 25
            path.write_text("Other provider sk-ant-" + "b" * 25 + "\nOpenAI: " + token)
            frontier.load_key_file(path)
            self.assertEqual(os.environ["OPENAI_API_KEY"], token)

    def test_existing_environment_takes_precedence(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-existing"}):
            frontier.load_key_file(Path("/nonexistent-key-file"))
            self.assertEqual(os.environ["OPENAI_API_KEY"], "test-existing")

    def test_ambiguous_or_unlabelled_key_is_rejected(self):
        token = "sk-" + "a" * 25
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "key-fixture.md"
            for text in (token, "OpenAI: " + token + "\nOpenAI: sk-" + "b"*25):
                with patch.dict(os.environ, {}, clear=True):
                    path.write_text(text)
                    with self.assertRaises(ValueError):
                        frontier.load_key_file(path)
                    self.assertNotIn("OPENAI_API_KEY", os.environ)


if __name__ == "__main__":
    unittest.main()

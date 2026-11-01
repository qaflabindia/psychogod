"""HTTP acceptance checks against the actual handler, SQLite archive and queue."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import app
import frontier
from forms import AssessmentBank
from records import Archive


class ParticipantFlow(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.server.assessments = AssessmentBank(app.ROOT)
        self.server.archive = Archive(Path(temp.name))
        self.addCleanup(self.server.archive.file_lock.close)
        thread = Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        status, self.form = self.request("/api/forms", {})
        self.assertEqual(status, 201)
        self.attempt = str(uuid4())
        self.answers = {q["id"]: f"Fictional response on {q['id']}." for q in self.form["questions"]}
        self.submit = "/api/forms/" + self.form["id"] + "/review"
        self.record = "/api/submissions/" + self.attempt

    def request(self, path, data=None, **headers):
        req = Request(self.base+path, data=None if data is None else json.dumps(data).encode(),
                      headers={"Content-Type": "application/json", **headers})
        try:
            with urlopen(req, timeout=5) as res:
                return res.status, json.load(res)
        except HTTPError as exc:
            with exc:
                return exc.code, json.load(exc)

    def test_submit_race_and_review_outage(self):
        payload = {"attemptId": self.attempt, "answers": self.answers}
        with ThreadPoolExecutor(max_workers=2) as pool:
            saves = list(pool.map(lambda _: self.request(self.submit, payload), range(2)))
        for code, result in saves:
            self.assertEqual((code,result["submissionId"]), (200,self.attempt))
        self.assertEqual(len(self.request("/api/submissions")[1]["submissions"]), 1)
        different = dict(self.answers)
        different[next(iter(different))] = "Changed."
        self.assertEqual(self.request(self.submit, {**payload,"answers":different})[0], 409)
        saved = self.request(self.record)[1]["items"]
        self.assertEqual([i["question"] for i in saved], self.form["questions"])
        self.assertEqual([i["answer"] for i in saved], list(self.answers.values()))
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            self.assertEqual(self.request(self.record+"/frontier", {})[0], 503)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fictional-test-only"}):
            self.assertEqual(self.request(self.record+"/frontier", {})[1]["queued"], 20)
            self.assertEqual(self.request(self.record+"/frontier", {})[1]["queued"], 0)
            error = HTTPError("https://api.openai.com/", 429, "Quota", {},
                              BytesIO(b'{"error":{"code":"insufficient_quota"}}'))
            with patch.object(frontier, "urlopen", side_effect=error) as transport:
                self.assertTrue(self.server.archive.run_one(frontier.review))
                self.assertFalse(self.server.archive.run_one(frontier.review))
                self.assertEqual(transport.call_count, 1)
        items = self.request(self.record)[1]["items"]
        self.assertIn("insufficient quota", items[0]["error"])
        self.assertTrue(all(i["state"]=="failed" and i["review"] is None for i in items))

    def test_invalid_and_cross_origin_requests_do_not_create_records(self):
        for invalid in ({}, dict.fromkeys(self.answers," "), dict.fromkeys(self.answers,"X"*10001)):
            self.assertEqual(self.request(self.submit, {"attemptId":self.attempt,"answers":invalid})[0], 400)
        self.assertEqual(self.request(self.submit, {"attemptId":self.attempt,"answers":self.answers},
                                      Origin="https://unrelated.example")[0], 403)
        self.assertEqual(self.request("/api/submissions")[1]["submissions"], [])
        self.assertEqual(self.request("/secret/keys.md")[0], 404)

    def test_all_reviews_are_saved_once_with_confirmed_model_and_evidence(self):
        self.request(self.submit, {"attemptId": self.attempt, "answers": self.answers})
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fictional-test-only"}):
            self.request(self.record+"/frontier", {})
            def provider(req, **kwargs):
                payload = json.loads(req.data)
                self.assertEqual(payload["model"], frontier.MODEL)
                self.assertFalse(payload["store"])
                rows = [{"criterion": i, "score": 1, "evidence": [1], "conflict": 0,
                         "feedback": "Mocked transport check only."} for i in range(1,4)]
                return BytesIO(json.dumps({"id": "resp_fixture", "model": frontier.MODEL,
                    "status": "completed", "output": [{"type": "message", "content": [
                    {"type": "output_text", "text": json.dumps({"ratings": rows})}]}]}).encode())
            with patch.object(frontier, "urlopen", side_effect=provider) as transport:
                while self.server.archive.run_one(frontier.review):
                    pass
                self.assertEqual(transport.call_count, 20)
                self.assertEqual(self.request(self.record+"/frontier", {})[1]["queued"], 0)
                self.assertFalse(self.server.archive.run_one(frontier.review))
        saved = self.request(self.record)[1]["items"]
        for item in saved:
            self.assertEqual(item["state"], "complete")
            self.assertEqual(item["review"]["model"], frontier.MODEL)
            self.assertEqual(item["review"]["ratings"][0]["quote"], item["answer"])

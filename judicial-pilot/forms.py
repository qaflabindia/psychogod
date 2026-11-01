"""Versioned, balanced forms for fictional judicial education exercises."""
import base64
import hashlib
import json
import re
import secrets
import struct
from pathlib import Path

CASE_COUNT = 10
DEVELOPMENT_COUNT = 5
TASK_COUNT = 4
PER_CATEGORY = CASE_COUNT * DEVELOPMENT_COUNT * TASK_COUNT
CATEGORY_COUNT = 20
RANDOM = secrets.SystemRandom()


def distinct_text(values, expected):
    if len(values) != expected or any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError("Incomplete category content")
    if len({value.strip().casefold() for value in values}) != expected:
        raise ValueError("Duplicate category content")


class AssessmentBank:
    def __init__(self, root: Path):
        self.categories = [
            category for file in ("categories-a.json", "categories-b.json")
            for category in json.loads((root / file).read_text())
        ]
        if [c["id"] for c in self.categories] != [f"C{n:02d}" for n in range(1, CATEGORY_COUNT + 1)]:
            raise ValueError("Expected 20 ordered categories")
        distinct_text([c["title"] for c in self.categories], CATEGORY_COUNT)
        for c in self.categories:
            for field in ("title", "record", "decision"):
                values = [case[field] for case in c["cases"]]
                if field == "decision":  # A common decision is legitimate for different records.
                    if not all(isinstance(value, str) and value.strip() for value in values):
                        raise ValueError("Missing decision")
                else:
                    distinct_text(values, CASE_COUNT)
            distinct_text(c["developments"], DEVELOPMENT_COUNT)
            distinct_text(c["tasks"], TASK_COUNT)
            distinct_text([row["name"] for row in c["criteria"]], 3)
            for row in c["criteria"]:
                distinct_text([row[key] for key in ("zero", "one", "two")], 3)
        content = json.dumps(self.categories, sort_keys=True, ensure_ascii=False).encode()
        self.version = "v1-" + hashlib.sha256(content).hexdigest()[:12]

    def question(self, index):
        cat, offset = divmod(index, PER_CATEGORY)
        case_no, variation = divmod(offset, DEVELOPMENT_COUNT * TASK_COUNT)
        development, task = divmod(variation, TASK_COUNT)
        category = self.categories[cat]
        record = category["cases"][case_no]
        return {"id": f"{category['id']}-{offset + 1:03d}", "category": category["title"],
                "title": record["title"], "record": record["record"], "decision": record["decision"],
                "development": category["developments"][development], "task": category["tasks"][task]}

    def new_form(self):
        indices = [c * PER_CATEGORY + RANDOM.randrange(PER_CATEGORY) for c in range(CATEGORY_COUNT)]
        RANDOM.shuffle(indices)
        packed = struct.pack(">20H", *indices)
        token = base64.urlsafe_b64encode(packed).decode().rstrip("=")
        return self.replay(self.version + "." + token)

    def replay(self, form_id):
        pattern = re.escape(self.version) + r"\.([A-Za-z0-9_-]{54})"
        match = re.fullmatch(pattern, form_id)
        if not match:
            raise ValueError("Unknown bank version or malformed form ID")
        data = base64.urlsafe_b64decode(match[1] + "==")
        if base64.urlsafe_b64encode(data).decode().rstrip("=") != match[1]:
            raise ValueError("Invalid form encoding")
        indices = struct.unpack(">20H", data)
        if {n // PER_CATEGORY for n in indices} != set(range(CATEGORY_COUNT)):
            raise ValueError("Invalid form composition")
        return {"id": form_id, "version": self.version, "questions": [self.question(n) for n in indices]}

    def rubric(self, question):
        return self.categories[int(question["id"][1:3]) - 1]["criteria"]

    def catalogue(self):
        return {"version": self.version, "total": CATEGORY_COUNT * PER_CATEGORY, "categories": [
            {"id": c["id"], "title": c["title"], "construct": c["construct"], "count": PER_CATEGORY}
            for c in self.categories]}

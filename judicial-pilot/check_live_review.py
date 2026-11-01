"""Opt-in, billable acceptance check on two synthetic answers. No archive writes."""
import argparse
from pathlib import Path

from forms import AssessmentBank
import frontier


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openai-key-file", type=Path)
    args = parser.parse_args()
    if args.openai_key_file:
        frontier.load_key_file(args.openai_key_file)
    if not frontier.configured():
        parser.exit(2, "Configure an OpenAI API key to run this check.\n")
    bank = AssessmentBank(Path(__file__).resolve().parent)
    question = bank.question(0)
    probes = [
        ("withdrawn order", "The delegated officer shall sign a sanction today and the registry shall monitor payment. "
         "I withdraw those directions. Send the representation to both agencies to consider in due course. "
         "The petition is closed and there is no return date.", 0),
        ("enforceable order", "Both agencies accept the delegation. The named officer must decide sanction within two working days "
         "on the accepted qualifying service. Treasury must give the officer the beneficiary match tomorrow. "
         "If the match is disputed, give the widow the discrepancy and hear her before an adverse decision. "
         "Treasury shall pay within five working days of sanction and send confirmation to the widow and registry. "
         "Keep the petition open and list on day eight on default without a fresh filing.", 2),
    ]
    passed = True
    for name, answer, expected in probes:
        try:
            result = frontier.review({"question": question, "criteria": bank.rubric(question), "answer": answer})
        except RuntimeError as exc:
            parser.exit(2, f"{name}: {exc} No verified score.\n")
        marks = [row["score"] for row in result["ratings"]]
        print(name, result["model"], result["responseId"], marks, flush=True)
        passed &= marks[2] == expected
    if not passed:
        parser.exit(1, "Effective-remedy ratings did not match the predeclared expectations.\n")


if __name__ == "__main__":
    main()

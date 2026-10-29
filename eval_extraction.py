"""
Eval: send every message in data/examples.jsonl to Gemini and check the answers.

Run with:  uv run python eval_extraction.py
"""
import datetime
import json
from pathlib import Path

from extraction import extract_request

EXAMPLES_FILE = Path(__file__).parent / "data" / "examples.jsonl"


def load_examples():
    # One test per line; empty lines are skipped
    examples = []
    with open(EXAMPLES_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def same(got, expected):
    # Gemini's dates are date objects, the file has text like "2027-06-10"
    if isinstance(got, datetime.date):
        got = got.isoformat()
    # For lists (interests) the order doesn't matter
    if isinstance(got, list) and isinstance(expected, list):
        return sorted(got) == sorted(expected)
    return got == expected


examples = load_examples()
messages_ok = 0
fields_ok = 0
fields_total = 0

for ex in examples:
    short = ex["message"][:60]                  # keep the printout readable
    fields_total += len(ex["expected"])

    try:
        request = extract_request(ex["message"])
    except Exception as e:
        print(f"❌ {short}\n     Gemini call failed: {type(e).__name__}")
        continue

    wrong = []
    for field, expected in ex["expected"].items():
        got = getattr(request, field, "<no such field>")
        if same(got, expected):
            fields_ok += 1
        else:
            wrong.append(f"{field}: got {got!r}, expected {expected!r}")

    if wrong:
        print(f"❌ {short}")
        for w in wrong:
            print("     " + w)
    else:
        messages_ok += 1
        print(f"✅ {short}")

print()
print(f"Messages fully correct: {messages_ok} / {len(examples)}")
print(f"Fields correct:         {fields_ok} / {fields_total}")
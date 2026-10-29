from extraction import extract_request


messages = [
    "Plan a trip for me, Alex and Raya from 10 to 15 June, 500 euros each. "
    "We loved Barcelona but want somewhere cheaper with great food.",
    "I want good restaurants and nice weather, max 3 hours away.",
    "Somewhere with beaches and bars this summer.",
    "A weekend trip from 28 to 31 October.",
    "One day trip on 10 October.",
]

for message in messages:
    print("USER:", message)
    print("  ->", extract_request(message))
    print()
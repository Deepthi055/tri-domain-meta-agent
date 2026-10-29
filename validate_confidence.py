
import math
from core.intent_detector import detect_intent
from test_queries import DATASETS

# Use the dataset containing your current 350 queries.
# Change "combined" if your 350-query dataset has another name.
queries = DATASETS["combined"]

print("Number of test queries:", len(queries))

results = []
skipped = 0

for test in queries:
    # Confidence validation applies to domain-routing examples.
    if test.get("expected_status", "success") != "success":
        skipped += 1
        continue

    expected = set(test.get("expected_domains", []))
    result = detect_intent(test.get("query", ""))

    predicted = set(result.get("domains", []))
    confidence = float(result.get("confidence", 0.0))

    results.append({
        "category": test.get("category", "unknown"),
        "confidence": confidence,
        "correct": expected == predicted,
        "expected": expected,
        "predicted": predicted,
    })

if not results:
    raise ValueError("No eligible domain-routing queries found.")

accuracy = sum(r["correct"] for r in results) / len(results)

print(f"\nEvaluated: {len(results)}")
print(f"Skipped non-success cases: {skipped}")
print(f"Exact-match accuracy: {accuracy:.2%}")

print("\nConfidence bucket analysis:")
buckets = [
    (0.0, 0.4),
    (0.4, 0.6),
    (0.6, 0.8),
    (0.8, 1.001),
]

for lower, upper in buckets:
    group = [
        r for r in results
        if lower <= r["confidence"] < upper
    ]

    if group:
        group_accuracy = sum(
            r["correct"] for r in group
        ) / len(group)

        avg_confidence = sum(
            r["confidence"] for r in group
        ) / len(group)

        print(
            f"{lower:.1f}-{min(upper, 1.0):.1f}: "
            f"n={len(group)}, "
            f"accuracy={group_accuracy:.2%}, "
            f"mean confidence={avg_confidence:.3f}"
        )

print("\nPer-category confidence analysis:")
categories = sorted({r["category"] for r in results})

for category in categories:
    group = [
        r for r in results if r["category"] == category
    ]

    correct = sum(r["correct"] for r in group)
    avg_conf = sum(
        r["confidence"] for r in group
    ) / len(group)

    print(
        f"{category}: "
        f"{correct}/{len(group)} correct, "
        f"accuracy={correct / len(group):.2%}, "
        f"mean confidence={avg_conf:.3f}"
    )

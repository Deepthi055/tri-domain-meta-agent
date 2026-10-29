
import math
from collections import defaultdict

from core.intent_detector import detect_intent
from core.safety_layer import extract_domain_signals
from test_queries import DATASETS


def old_confidence(scores):
    values = [max(0, float(scores.get(d, 0)))
              for d in ("career", "health", "finance")]
    total = sum(values)

    if total == 0:
        return 0.0

    probabilities = [v / total for v in values]
    entropy = -sum(p * math.log(p) for p in probabilities if p > 0)
    return round(1 - entropy / math.log(3), 3)


def candidate_score(scores):
    """Experimental score: match strength and separation."""
    values = [max(0, float(scores.get(d, 0)))
              for d in ("career", "health", "finance")]
    ordered = sorted(values, reverse=True)
    top, second = ordered[0], ordered[1]
    total = sum(values)

    if top == 0:
        return 0.0

    # Match strength increases with keyword evidence.
    strength = top / (top + 2)

    # Separation is high when the leading domain stands apart.
    separation = (top - second) / top

    return round(strength * separation, 3)


def main():
    results = []

    for item in DATASETS["combined"]:
        if item.get("expected_status", "success") != "success":
            continue

        query = item.get("query", "")
        expected = set(item.get("expected_domains", []))

        # Compare the detector's prediction against the labelled domains.
        prediction = set(detect_intent(query).get("domains", []))
        if not expected:
            continue

        _, scores, _ = extract_domain_signals(query)

        results.append({
            "category": item.get("category", "unknown"),
            "correct": prediction == expected,
            "old": old_confidence(scores),
            "candidate": candidate_score(scores),
        })

    print(f"Evaluated queries: {len(results)}")
    if not results:
        print("No eligible queries found. Check dataset labels and statuses.")
        return

    for name in ("old", "candidate"):
        buckets = defaultdict(list)

        for row in results:
            score = row[name]
            bucket = min(int(score * 5), 4)
            buckets[bucket].append(row)

        print(f"\n{name.upper()} SCORE")
        for bucket in range(5):
            rows = buckets[bucket]
            if not rows:
                continue

            accuracy = sum(r["correct"] for r in rows) / len(rows)
            print(
                f"{bucket * 0.2:.1f}-{(bucket + 1) * 0.2:.1f}: "
                f"n={len(rows)}, accuracy={accuracy:.1%}, "
                f"mean score={sum(r[name] for r in rows) / len(rows):.3f}"
            )


if __name__ == "__main__":
    main()

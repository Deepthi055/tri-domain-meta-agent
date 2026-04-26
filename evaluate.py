import requests
import json
import time
from test_queries import TEST_QUERIES

API = "http://127.0.0.1:8000"

BASE_PROFILE = {
    "name": "TestUser",
    "age": 28,
    "weight_kg": 75,
    "height_cm": 175,
    "monthly_income": 50000,
    "monthly_expenses": 35000,
    "current_skills": ["python", "sql"],
    "target_role": "data scientist"
}

results = []
correct = 0
total = len(TEST_QUERIES)
latencies = []

print(f"\nRunning {total} test queries...\n")
print(f"{'ID':<6} {'Category':<15} {'Expected':<25} {'Got':<25} {'ms':<8} {'Pass'}")
print("─" * 100)

for test in TEST_QUERIES:
    payload = {**BASE_PROFILE, "query": test["query"]}

    try:
        # ── Latency measured HERE inside the loop ──
        start = time.time()
        res = requests.post(f"{API}/query", json=payload, timeout=30)
        end = time.time()
        latency = round((end - start) * 1000)
        latencies.append(latency)

        data = res.json()

        actual_status = data.get("status", "success")
        actual_domains = sorted(data.get("domains_activated", []))
        expected_domains = sorted(test.get("expected_domains", []))
        expected_status = test.get("expected_status", "success")

        if expected_status in ["blocked", "out_of_scope"]:
            passed = actual_status in ["blocked", "out_of_scope"]
        else:
            passed = actual_domains == expected_domains

        if passed:
            correct += 1
            status_str = "PASS"
        else:
            status_str = "FAIL"

        print(f"{test['id']:<6} {test['category']:<15} {str(expected_domains):<25} {str(actual_domains):<25} {latency:<8} {status_str}")

        results.append({
            "id": test["id"],
            "category": test["category"],
            "query": test["query"],
            "expected": expected_domains,
            "actual": actual_domains,
            "latency_ms": latency,
            "passed": passed
        })

    except Exception as e:
        print(f"{test['id']:<6} ERROR: {e}")
        results.append({
            "id": test["id"],
            "category": test["category"],
            "passed": False,
            "error": str(e)
        })

# ── Summary ───────────────────────────────────────────────────
accuracy = (correct / total) * 100

print("\n" + "═" * 100)
print(f"\nOverall accuracy: {correct}/{total} = {accuracy:.1f}%")

# Per category breakdown
categories = {}
for r in results:
    cat = r["category"]
    if cat not in categories:
        categories[cat] = {"correct": 0, "total": 0, "latencies": []}
    categories[cat]["total"] += 1
    if r["passed"]:
        categories[cat]["correct"] += 1
    if "latency_ms" in r:
        categories[cat]["latencies"].append(r["latency_ms"])

print("\nPer-category breakdown:")
print(f"  {'Category':<22} {'Accuracy':<15} {'Avg latency'}")
print("  " + "─" * 50)
for cat, counts in categories.items():
    cat_acc = (counts["correct"] / counts["total"]) * 100
    avg_lat = round(sum(counts["latencies"]) / len(counts["latencies"])) if counts["latencies"] else 0
    print(f"  {cat:<22} {counts['correct']}/{counts['total']} = {cat_acc:<6.0f}%   {avg_lat}ms")

# Overall latency stats
if latencies:
    print(f"\nLatency summary:")
    print(f"  Fastest:  {min(latencies)}ms")
    print(f"  Slowest:  {max(latencies)}ms")
    print(f"  Average:  {round(sum(latencies)/len(latencies))}ms")

# Save results
with open("evaluation_results.json", "w") as f:
    json.dump({
        "total": total,
        "correct": correct,
        "accuracy_pct": round(accuracy, 1),
        "avg_latency_ms": round(sum(latencies)/len(latencies)) if latencies else 0,
        "per_category": {
            k: {
                "correct": v["correct"],
                "total": v["total"],
                "accuracy_pct": round((v["correct"]/v["total"])*100, 1),
                "avg_latency_ms": round(sum(v["latencies"])/len(v["latencies"])) if v["latencies"] else 0
            }
            for k, v in categories.items()
        },
        "details": results
    }, f, indent=2)

print(f"\nResults saved to evaluation_results.json")
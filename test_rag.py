from rag.retriever import retrieve

queries = [
    "How do I become a data scientist?",
    "What salary can I expect as a data scientist in Bangalore?",
    "How do I handle job stress during career transition?",
    "How long does it take to switch careers?"
]

for q in queries:
    print(f"\nQuery: {q}")
    print("─" * 60)
    results = retrieve(q, top_k=2)
    for r in results:
        print(f"[Score: {r['relevance_score']}] {r['source']}")
        print(r['text'][:200] + "...")
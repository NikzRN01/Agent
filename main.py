"""Minimal runner for the Agent project."""
from core.orchestrator import Orchestrator


def main():
    orch = Orchestrator()
    recs = orch.recommend(top=3)
    print("Top recommendations:")
    for r in recs:
        print(f"- {r.get('title')} (ingredients: {', '.join(r.get('ingredients', []))})")


if __name__ == "__main__":
    main()

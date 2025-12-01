import json
from pathlib import Path

from agents import RecipeAgent, PreferenceAgent, ShoppingBudgetAgent, HealthAgent


class Orchestrator:
    def __init__(self, data_path=None, preferences=None, budget=None):
        self.data_path = Path(data_path) if data_path else Path(__file__).parent.parent / "data" / "sample_recipes.json"
        self.preferences = preferences or {}
        self.budget = budget
        self._load()

    def _load(self):
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                recipes = json.load(f)
        except Exception:
            recipes = []
        self.recipe_agent = RecipeAgent(recipes)
        self.pref_agent = PreferenceAgent(self.preferences)
        self.budget_agent = ShoppingBudgetAgent(self.budget)
        self.health_agent = HealthAgent()

    def recommend(self, top=5):
        recipes = self.recipe_agent.list_recipes()
        recipes = self.pref_agent.filter_recipes(recipes)
        # score by health_agent then limit
        scored = []
        for r in recipes:
            score = self.health_agent.score_recipe(r)
            cost = self.budget_agent.estimate_cost(r)
            scored.append((score, cost, r))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [r for _, _, r in scored[:top]]

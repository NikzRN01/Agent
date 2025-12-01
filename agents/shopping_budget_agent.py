class ShoppingBudgetAgent:
    """Basic budget agent to estimate shopping cost."""
    def __init__(self, budget=None):
        self.budget = budget or 0.0

    def estimate_cost(self, recipe):
        # naive stub: count ingredients as cost units
        ing = recipe.get("ingredients", [])
        return len(ing) * 2.5

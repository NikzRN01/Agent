class RecipeAgent:
    """Agent that holds and serves recipes."""
    def __init__(self, recipes=None):
        self.recipes = recipes or []

    def list_recipes(self):
        return self.recipes

class HealthAgent:
    """Very small health agent that scores recipes."""
    def __init__(self):
        pass

    def score_recipe(self, recipe):
        # higher score for more vegetables (very naive)
        ingredients = recipe.get("ingredients", [])
        veg_keywords = {"lettuce","spinach","kale","broccoli","carrot","pepper","tomato"}
        count = sum(1 for i in ingredients if any(v in i.lower() for v in veg_keywords))
        return count

class PreferenceAgent:
    """Simple preference agent placeholder."""
    def __init__(self, preferences=None):
        self.preferences = preferences or {}

    def filter_recipes(self, recipes):
        """Return recipes that match simple preferences (e.g., exclude ingredients)."""
        exclude = set(self.preferences.get("exclude_ingredients", []))
        if not exclude:
            return recipes
        filtered = []
        for r in recipes:
            ingredients = set(r.get("ingredients", []))
            if ingredients & exclude:
                continue
            filtered.append(r)
        return filtered

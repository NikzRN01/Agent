import json
from pathlib import Path
from typing import List
from models.schema import Meal, Ingredient, MealNutrition, UserHealthProfile


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class RecipeAgent:
    """
    Fetches recipes based on preferences and returns Meal objects.
    Currently uses local JSON + simple fake macro calculation.
    """

    def __init__(self):
        self._recipes = self._load_recipes()

    def _load_recipes(self) -> List[Meal]:
        path = DATA_DIR / "sample_recipes.json"
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        meals: List[Meal] = []
        for r in raw:
            ingredients = [Ingredient(**ing) for ing in r["ingredients"]]
            meals.append(Meal(id=r["id"], name=r["name"], ingredients=ingredients, servings=1))
        return meals

    def _fake_nutrition_lookup(self, ingredient: Ingredient) -> MealNutrition:
        """
        TEMP: approximate macros per 100g / piece.
        Replace this with a real nutrition API client.
        """
        name = ingredient.name.lower()
        if "tofu" in name:
            base = MealNutrition(calories=76, protein_g=8, carbs_g=1.9, fat_g=4.8)
        elif "oats" in name:
            base = MealNutrition(calories=389, protein_g=17, carbs_g=66, fat_g=7)
        elif "banana" in name:
            base = MealNutrition(calories=105, protein_g=1.3, carbs_g=27, fat_g=0.3)
        elif "olive oil" in name:
            base = MealNutrition(calories=884, protein_g=0, carbs_g=0, fat_g=100)
        else:
            base = MealNutrition(calories=50, protein_g=2, carbs_g=10, fat_g=1)

        # scale by quantity (assume 100 g or 1 piece reference)
        factor = ingredient.quantity / 100.0 if ingredient.unit in ("g", "ml") else ingredient.quantity
        return MealNutrition(
            calories=base.calories * factor,
            protein_g=base.protein_g * factor,
            carbs_g=base.carbs_g * factor,
            fat_g=base.fat_g * factor,
        )

    def _compute_meal_macros(self, meal: Meal) -> Meal:
        total = MealNutrition(calories=0, protein_g=0, carbs_g=0, fat_g=0)
        for ing in meal.ingredients:
            m = self._fake_nutrition_lookup(ing)
            total.calories += m.calories
            total.protein_g += m.protein_g
            total.carbs_g += m.carbs_g
            total.fat_g += m.fat_g
        meal.macros_per_serving = total
        return meal

    def generate_week_plan(self, profile: UserHealthProfile) -> "WeekPlan":
        """
        Very simple planner: repeat first N meals across 7 days.
        Later you can make this smart with LLM reasoning.
        """
        from models.schema import DayPlan, WeekPlan

        meals_with_macros = [self._compute_meal_macros(m) for m in self._recipes]
        days: List[DayPlan] = []

        for i in range(7):
            # naive: same two meals every day (replace with variety logic)
            day_meals = meals_with_macros[:profile.meals_per_day]
            days.append(DayPlan(day_name=f"Day {i + 1}", meals=day_meals))

        return WeekPlan(days=days)

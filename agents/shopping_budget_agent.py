from collections import defaultdict
from typing import Dict
from models.schema import WeekPlan, Ingredient, UserHealthProfile


class ShoppingBudgetAgent:
    """
    Aggregates ingredients for the week and does a simple budget estimation.
    Replace cost logic with real store APIs later.
    """

    def build_grocery_list(self, week_plan: WeekPlan) -> Dict[str, Ingredient]:
        aggregated: Dict[str, Ingredient] = {}

        for day in week_plan.days:
            for meal in day.meals:
                for ing in meal.ingredients:
                    key = ing.name.lower()
                    if key not in aggregated:
                        aggregated[key] = Ingredient(
                            name=ing.name, quantity=ing.quantity, unit=ing.unit
                        )
                    else:
                        aggregated[key].quantity += ing.quantity
        return aggregated

    def estimate_cost(self, grocery_list: Dict[str, Ingredient]) -> float:
        """
        TEMP: assign a flat price per 100g/item.
        Later, call grocery APIs or local price DB.
        """
        price_map = defaultdict(lambda: 0.5)  # default price
        price_map.update({
            "tofu": 0.8,
            "oats": 0.4,
            "banana": 0.2,
            "olive oil": 1.0,
        })

        total_cost = 0.0
        for name, ing in grocery_list.items():
            unit_price = price_map[name]
            factor = ing.quantity / 100.0 if ing.unit in ("g", "ml") else ing.quantity
            total_cost += unit_price * factor
        return round(total_cost, 2)

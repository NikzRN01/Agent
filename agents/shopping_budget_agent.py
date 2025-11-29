"""
shopping_budget_agent.py

Shopping & Budget Agent for Meal Planner Project.

Responsibilities:
1. Take recipe ingredients (output of RecipeAgent).
2. Parse and aggregate ingredients from JSON format.
3. Look up or approximate prices per store (mock implementation for now).
4. Build a consolidated grocery list with best store choice per item.
5. Compare estimated total cost against user budget.
6. Suggest high-impact cost-saving changes if over budget.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from math import ceil
from typing import List, Dict, Tuple, Any, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()

print("✅ ShoppingBudgetAgent module loaded.")

# =========================
#   DATA STRUCTURES
# =========================

@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str


@dataclass
class Meal:
    type: str               # e.g. "breakfast", "lunch", "dinner"
    name: str
    servings: int
    ingredients: List[Ingredient]


@dataclass
class DayPlan:
    day: int                # 1..7
    meals: List[Meal]


@dataclass
class Menu:
    """Weekly menu – should match your RecipeAgent output structure."""
    days: List[DayPlan]


# =========================
#   SHOPPING & BUDGET AGENT
# =========================

class ShoppingBudgetAgent:
    """
    Shopping & Budget Agent

    Usage:
        agent = ShoppingBudgetAgent(currency="INR")
        # From Recipe Agent JSON:
        result = agent.process_recipe_ingredients(recipe_data, stores=["Amazon", "Flipkart"], budget=500)
        # From Menu structure:
        result = agent.build_shopping_plan(menu, stores=["Amazon", "Flipkart"], budget=2000)

    Result (dict) includes:
        - shopping_list: consolidated list of items with prices
        - estimated_total_cost
        - currency
        - budget
        - within_budget
        - amount_over_budget
        - recipe_change_suggestions
    """

    def __init__(self, currency: str = "INR") -> None:
        self.currency = currency
    
    # ---------- RECIPE AGENT JSON PROCESSING ----------
    
    def process_recipe_ingredients(
        self,
        recipe_data: Dict[str, Any],
        stores: List[str],
        budget: float,
    ) -> Dict[str, Any]:
        """
        Process ingredients from Recipe Agent's JSON format.
        
        Parameters
        ----------
        recipe_data : Dict[str, Any]
            JSON from Recipe Agent with structure:
            {
                "recipe_name": str,
                "ingredients": {
                    "Section Name": ["ingredient strings", ...],
                    ...
                }
            }
        stores : List[str]
            Stores to consider for pricing.
        budget : float
            User's budget for this recipe.
        
        Returns
        -------
        Dict[str, Any]
            Shopping plan with costs and suggestions.
        """
        # Parse ingredients from Recipe Agent JSON format
        parsed_ingredients = self._parse_recipe_json(recipe_data)
        
        # Convert to aggregate format
        aggregate = self._aggregate_parsed_ingredients(parsed_ingredients)
        
        # Build shopping list with prices
        shopping_list, total_cost = self._build_shopping_list_with_prices(
            aggregate=aggregate,
            stores=stores,
        )
        
        # Evaluate budget
        budget_info = self._evaluate_budget(
            shopping_list=shopping_list,
            total_cost=total_cost,
            budget=budget,
        )
        
        return {
            "recipe_name": recipe_data.get("recipe_name", "Unknown"),
            "shopping_list": shopping_list,
            "estimated_total_cost": total_cost,
            "currency": self.currency,
            "budget": budget,
            "within_budget": budget_info["within_budget"],
            "amount_over_budget": budget_info["amount_over_budget"],
            "recipe_change_suggestions": budget_info["recipe_change_suggestions"],
        }
    
    def _parse_recipe_json(self, recipe_data: Dict[str, Any]) -> List[Ingredient]:
        """
        Parse ingredients from Recipe Agent JSON format.
        
        Converts:
        {
            "For the Sauce": ["2 tablespoons olive oil", "1 onion, chopped"],
            "For the Pasta": ["1 pound pasta"]
        }
        
        To: List[Ingredient]
        """
        ingredients_list = []
        ingredients_dict = recipe_data.get("ingredients", {})
        
        for section_name, items in ingredients_dict.items():
            for item_str in items:
                # Parse ingredient string (e.g., "2 tablespoons olive oil")
                parsed = self._parse_ingredient_string(item_str)
                if parsed:
                    ingredients_list.append(parsed)
        
        return ingredients_list
    
    def _parse_ingredient_string(self, ingredient_str: str) -> Optional[Ingredient]:
        """
        Parse an ingredient string like "2 tablespoons olive oil" into components.
        
        Returns Ingredient or None if parsing fails.
        """
        import re
        
        # Pattern: optional number, optional unit, ingredient name
        # Examples: "2 tablespoons olive oil", "1 onion, chopped", "salt to taste"
        pattern = r'^([\d./]+)?\s*([a-zA-Z]+)?\s+(.+)$'
        match = re.match(pattern, ingredient_str.strip())
        
        if match:
            quantity_str = match.group(1)
            unit = match.group(2) if match.group(2) else "piece"
            name = match.group(3)
            
            # Parse quantity (handle fractions like 1/2)
            if quantity_str:
                if '/' in quantity_str:
                    parts = quantity_str.split('/')
                    quantity = float(parts[0]) / float(parts[1])
                else:
                    quantity = float(quantity_str)
            else:
                quantity = 1.0
            
            # Clean up name (remove descriptions after comma)
            name = name.split(',')[0].strip()
            
            return Ingredient(name=name, quantity=quantity, unit=unit)
        else:
            # Fallback: treat entire string as name with quantity 1
            return Ingredient(name=ingredient_str.strip(), quantity=1.0, unit="piece")
    
    def _aggregate_parsed_ingredients(self, ingredients: List[Ingredient]) -> Dict[Tuple[str, str], float]:
        """
        Aggregate parsed ingredients by (name, unit).
        """
        aggregate: Dict[Tuple[str, str], float] = {}
        
        for ing in ingredients:
            key = (ing.name.strip().lower(), ing.unit.lower())
            aggregate[key] = aggregate.get(key, 0.0) + ing.quantity
        
        return aggregate

    # ---------- PUBLIC ENTRY POINT ----------

    def build_shopping_plan(
        self,
        menu: Menu,
        stores: List[str],
        budget: float,
    ) -> Dict[str, Any]:
        """
        Main method called by the orchestrator.

        Parameters
        ----------
        menu : Menu
            Weekly menu generated by RecipeAgent.
        stores : List[str]
            Stores to consider for pricing (e.g., ["Amazon", "Flipkart"]).
        budget : float
            User's weekly grocery budget.

        Returns
        -------
        Dict[str, Any]
            {
              "shopping_list": [...],
              "estimated_total_cost": float,
              "currency": str,
              "budget": float,
              "within_budget": bool,
              "amount_over_budget": float,
              "recipe_change_suggestions": [...]
            }
        """
        # 1) Aggregate ingredients across all days/meals
        aggregate = self._aggregate_ingredients(menu)

        # 2) Create shopping list with best store options and total cost
        shopping_list, total_cost = self._build_shopping_list_with_prices(
            aggregate=aggregate,
            stores=stores,
        )

        # 3) Evaluate cost vs budget + suggestions
        budget_info = self._evaluate_budget(
            shopping_list=shopping_list,
            total_cost=total_cost,
            budget=budget,
        )

        return {
            "shopping_list": shopping_list,
            "estimated_total_cost": total_cost,
            "currency": self.currency,
            "budget": budget,
            "within_budget": budget_info["within_budget"],
            "amount_over_budget": budget_info["amount_over_budget"],
            "recipe_change_suggestions": budget_info["recipe_change_suggestions"],
        }

    # ---------- SHOPPING LOGIC ----------

    def _aggregate_ingredients(self, menu: Menu) -> Dict[Tuple[str, str], float]:
        """
        Combine all ingredients across the menu.

        Returns
        -------
        Dict[(ingredient_name_lower, unit), total_quantity]
        """
        aggregate: Dict[Tuple[str, str], float] = {}

        for day in menu.days:
            for meal in day.meals:
                for ing in meal.ingredients:
                    key = (ing.name.strip().lower(), ing.unit)
                    aggregate[key] = aggregate.get(key, 0.0) + ing.quantity

        return aggregate

    def _categorize_ingredient(self, item_name: str) -> str:
        """
        Categorize ingredient based on its name.
        
        Categories: vegetables, fruits, grains, dairy, protein, spices, oils, other
        """
        name = item_name.lower()
        
        # Vegetables
        vegetables = ["onion", "tomato", "potato", "bell pepper", "pepper", "zucchini", 
                     "carrot", "spinach", "lettuce", "cabbage", "broccoli", "cauliflower",
                     "mushroom", "garlic", "ginger", "celery", "cucumber"]
        
        # Fruits
        fruits = ["apple", "banana", "orange", "lemon", "lime", "mango", "berry", 
                 "strawberry", "grape", "pineapple"]
        
        # Grains & Pasta
        grains = ["rice", "pasta", "penne", "rigatoni", "spaghetti", "flour", "wheat",
                 "bread", "oats", "quinoa", "barley", "noodle"]
        
        # Dairy
        dairy = ["milk", "cheese", "mozzarella", "parmesan", "cheddar", "ricotta",
                "yogurt", "butter", "cream", "paneer"]
        
        # Protein
        protein = ["chicken", "beef", "pork", "fish", "salmon", "tuna", "egg",
                  "tofu", "lentil", "bean", "chickpea"]
        
        # Spices & Herbs
        spices = ["salt", "pepper", "chili", "oregano", "basil", "thyme", "rosemary",
                 "cumin", "coriander", "turmeric", "paprika", "cinnamon", "garam masala",
                 "bay leaf", "mint", "cilantro", "parsley", "fenugreek", "kasuri methi"]
        
        # Oils & Sauces
        oils = ["oil", "olive oil", "vegetable oil", "butter", "ghee", "sauce",
               "tomato sauce", "soy sauce", "vinegar", "paste", "tomato paste"]
        
        for veg in vegetables:
            if veg in name:
                return "vegetables"
        
        for fruit in fruits:
            if fruit in name:
                return "fruits"
        
        for grain in grains:
            if grain in name:
                return "grains"
        
        for d in dairy:
            if d in name:
                return "dairy"
        
        for p in protein:
            if p in name:
                return "protein"
        
        for spice in spices:
            if spice in name:
                return "spices"
        
        for o in oils:
            if o in name:
                return "oils"
        
        return "other"

    def _dynamic_price_lookup(
        self,
        item_name: str,
        unit: str,
        category: str,
        stores: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Dynamic price lookup based on ingredient category and typical market prices.
        
        This provides realistic price estimates based on category.
        Can be replaced with actual API calls to Amazon/Flipkart.
        
        Returns
        -------
        List of store options with prices
        """
        # Default package sizes and base prices by category (in INR)
        category_pricing = {
            "vegetables": {
                "base_price": 40,
                "package_size": 500,
                "package_unit": "gram",
                "price_variance": 0.3  # 30% price variation between stores
            },
            "fruits": {
                "base_price": 60,
                "package_size": 500,
                "package_unit": "gram",
                "price_variance": 0.25
            },
            "grains": {
                "base_price": 50,
                "package_size": 1000,
                "package_unit": "gram",
                "price_variance": 0.2
            },
            "dairy": {
                "base_price": 180,
                "package_size": 200,
                "package_unit": "gram",
                "price_variance": 0.15
            },
            "protein": {
                "base_price": 250,
                "package_size": 500,
                "package_unit": "gram",
                "price_variance": 0.25
            },
            "spices": {
                "base_price": 30,
                "package_size": 50,
                "package_unit": "gram",
                "price_variance": 0.4
            },
            "oils": {
                "base_price": 150,
                "package_size": 500,
                "package_unit": "ml",
                "price_variance": 0.2
            },
            "other": {
                "base_price": 100,
                "package_size": 500,
                "package_unit": unit,
                "price_variance": 0.3
            }
        }
        
        pricing_info = category_pricing.get(category, category_pricing["other"])
        
        # Generate prices for different stores with variance
        import random
        random.seed(hash(item_name))  # Consistent prices for same item
        
        store_options = []
        default_stores = stores if stores else ["Amazon", "Flipkart", "LocalStore"]
        
        for i, store in enumerate(default_stores[:3]):  # Max 3 stores
            variance = pricing_info["price_variance"]
            price_multiplier = 1 + random.uniform(-variance, variance)
            
            store_options.append({
                "store": store,
                "package_size": pricing_info["package_size"],
                "package_unit": pricing_info["package_unit"],
                "price": round(pricing_info["base_price"] * price_multiplier, 2)
            })
        
        return store_options

    def _build_shopping_list_with_prices(
        self,
        aggregate: Dict[Tuple[str, str], float],
        stores: List[str],
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        For each ingredient, choose cheapest store option and compute total cost.
        Uses dynamic pricing based on ingredient category.

        Returns
        -------
        shopping_list : List[Dict[str, Any]]
        total_cost    : float
        """
        shopping_list: List[Dict[str, Any]] = []
        total_cost = 0.0

        for (name, unit), qty in aggregate.items():
            # Categorize the ingredient
            category = self._categorize_ingredient(name)
            
            # Get price options from different stores
            options_raw = self._dynamic_price_lookup(name, unit, category, stores)

            store_options = []
            best_cost = None
            best_option = None

            for opt in options_raw:
                packages_needed = ceil(qty / opt["package_size"])
                effective_cost = packages_needed * opt["price"]

                store_options.append(
                    {
                        "store": opt["store"],
                        "package_size": opt["package_size"],
                        "package_unit": opt["package_unit"],
                        "price": opt["price"],
                        "currency": self.currency,
                    }
                )

                if best_cost is None or effective_cost < best_cost:
                    best_cost = effective_cost
                    best_option = {
                        "chosen_store": opt["store"],
                        "packages_needed": packages_needed,
                        "chosen_price": opt["price"],
                        "effective_cost": effective_cost,
                    }

            total_cost += best_cost or 0.0

            shopping_list.append(
                {
                    "item": name,
                    "category": category,
                    "required_quantity": qty,
                    "unit": unit,
                    "store_options": store_options,
                    **best_option,
                }
            )

        return shopping_list, total_cost

    # ---------- BUDGET LOGIC ----------

    def _evaluate_budget(
        self,
        shopping_list: List[Dict[str, Any]],
        total_cost: float,
        budget: float,
    ) -> Dict[str, Any]:
        """
        Compare total_cost vs budget and generate intelligent cost-saving suggestions
        based on ingredient categories.
        """
        within_budget = total_cost <= budget
        amount_over_budget = max(0.0, total_cost - budget)

        recipe_change_suggestions: List[Dict[str, Any]] = []

        if not within_budget:
            # Identify expensive items by category
            expensive_items = sorted(
                shopping_list, 
                key=lambda x: x["effective_cost"], 
                reverse=True
            )
            
            # Generate smart suggestions based on category
            suggestions_made = 0
            for item in expensive_items:
                if suggestions_made >= 5:  # Limit to top 5 suggestions
                    break
                
                category = item["category"]
                item_name = item["item"]
                cost = item["effective_cost"]
                
                suggestion = None
                
                if category == "dairy" and cost > 100:
                    suggestion = {
                        "impact": "high",
                        "category": category,
                        "item": item_name,
                        "description": f"Consider reducing '{item_name}' quantity or using a cheaper alternative like plant-based options.",
                        "estimated_savings": round(0.4 * cost, 2),
                    }
                elif category == "protein" and cost > 150:
                    suggestion = {
                        "impact": "high",
                        "category": category,
                        "item": item_name,
                        "description": f"Replace '{item_name}' with more economical protein sources like lentils, chickpeas, or eggs.",
                        "estimated_savings": round(0.5 * cost, 2),
                    }
                elif category == "vegetables" and cost > 80:
                    suggestion = {
                        "impact": "medium",
                        "category": category,
                        "item": item_name,
                        "description": f"Buy '{item_name}' from local markets instead of premium stores for better prices.",
                        "estimated_savings": round(0.25 * cost, 2),
                    }
                elif category == "grains" and cost > 100:
                    suggestion = {
                        "impact": "medium",
                        "category": category,
                        "item": item_name,
                        "description": f"Purchase '{item_name}' in bulk quantities to reduce per-unit cost.",
                        "estimated_savings": round(0.3 * cost, 2),
                    }
                elif cost > 50:  # General expensive items
                    suggestion = {
                        "impact": "low",
                        "category": category,
                        "item": item_name,
                        "description": f"Consider reducing '{item_name}' quantity or finding cheaper alternatives.",
                        "estimated_savings": round(0.2 * cost, 2),
                    }
                
                if suggestion:
                    recipe_change_suggestions.append(suggestion)
                    suggestions_made += 1
            
            # Add overall budget tip
            if amount_over_budget > 0:
                recipe_change_suggestions.insert(0, {
                    "impact": "critical",
                    "category": "budget",
                    "item": "Overall Budget",
                    "description": f"You are ₹{round(amount_over_budget, 2)} over budget. Consider implementing the suggestions below to reduce costs.",
                    "estimated_savings": round(sum(s.get("estimated_savings", 0) for s in recipe_change_suggestions), 2),
                })

        return {
            "within_budget": within_budget,
            "amount_over_budget": amount_over_budget,
            "recipe_change_suggestions": recipe_change_suggestions,
        }


# =========================
#   SIMPLE DEMO / TEST
# =========================

if __name__ == "__main__":
    # Minimal example to test the agent independently.

    # Build a tiny fake menu similar to what RecipeAgent would output
    breakfast = Meal(
        type="breakfast",
        name="Masala Oats",
        servings=2,
        ingredients=[
            Ingredient(name="Oats", quantity=50, unit="gram"),
            Ingredient(name="Onion", quantity=0.5, unit="piece"),
        ],
    )

    dinner = Meal(
        type="dinner",
        name="Paneer Curry",
        servings=2,
        ingredients=[
            Ingredient(name="Paneer", quantity=80, unit="gram"),
            Ingredient(name="Tomato", quantity=0.5, unit="piece"),
        ],
    )

    menu = Menu(
        days=[
            DayPlan(day=1, meals=[breakfast, dinner]),
            DayPlan(day=2, meals=[breakfast, dinner]),
        ]
    )

    agent = ShoppingBudgetAgent(currency="INR")

    result = agent.build_shopping_plan(
        menu=menu,
        stores=["Amazon", "Flipkart"],
        budget=500,  # weekly budget
    )

    # Pretty-print result
    from pprint import pprint
    pprint(result)
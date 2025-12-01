from models.schema import WeekPlan, WeekHealthReport
from agents.preference_agent import PreferenceAgent
from agents.recipe_agent import RecipeAgent
from agents.shopping_budget_agent import ShoppingBudgetAgent
from agents.health_agent import HealthAgent


class MealPlanningOrchestrator:
    def __init__(self):
        self.preference_agent = PreferenceAgent()
        self.recipe_agent = RecipeAgent()
        self.shopping_agent = ShoppingBudgetAgent()
        self.health_agent = HealthAgent()

    def run_weekly_planning(self) -> tuple[WeekPlan, WeekHealthReport, float]:
        # 1. Get user profile
        profile = self.preference_agent.get_user_profile()

        # 2. Generate candidate week plan (recipes + macros)
        week_plan = self.recipe_agent.generate_week_plan(profile)

        # 3. Build grocery list + estimate budget
        grocery_list = self.shopping_agent.build_grocery_list(week_plan)
        estimated_cost = self.shopping_agent.estimate_cost(grocery_list)

        # 4. Evaluate health alignment
        health_report = self.health_agent.evaluate_week(week_plan, profile)

        # For now, we only log; later, you can loop and refine plan.
        return week_plan, health_report, estimated_cost

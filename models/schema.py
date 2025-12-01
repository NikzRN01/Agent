from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class UserHealthProfile(BaseModel):
    diet_type: str = "vegetarian"
    daily_calorie_target: int = 2200
    protein_target_g: int = 100
    carb_target_g: int = 230
    fat_target_g: int = 70
    meals_per_day: int = 3
    allergies: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    health_notes: List[str] = Field(default_factory=list)


class Ingredient(BaseModel):
    name: str
    quantity: float          # numeric quantity
    unit: str                # e.g. "g", "cup", "piece"


class MealNutrition(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class Meal(BaseModel):
    id: str
    name: str
    ingredients: List[Ingredient]
    macros_per_serving: Optional[MealNutrition] = None
    servings: int = 1


class DayPlan(BaseModel):
    day_name: str
    meals: List[Meal]


class WeekPlan(BaseModel):
    days: List[DayPlan]


class DayHealthReport(BaseModel):
    day_name: str
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    calorie_delta: float
    protein_delta: float
    carb_delta: float
    fat_delta: float
    score: float
    flags: List[str]


class WeekHealthReport(BaseModel):
    daily_reports: List[DayHealthReport]
    average_score: float
    global_flags: List[str]

from models.schema import UserHealthProfile


class PreferenceAgent:
    """
    Collects user preferences and returns a structured UserHealthProfile.
    In the real system, this would ask questions or use an LLM.
    """

    def get_user_profile(self) -> UserHealthProfile:
        # TODO: replace with actual interaction / LLM parsing
        profile = UserHealthProfile(
            diet_type="vegetarian",
            daily_calorie_target=2200,
            protein_target_g=100,
            carb_target_g=230,
            fat_target_g=70,
            meals_per_day=3,
            allergies=["peanut"],
            dislikes=["broccoli"],
            health_notes=["low_sugar"]
        )
        return profile

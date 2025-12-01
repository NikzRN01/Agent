from typing import List
from models.schema import (
    UserHealthProfile,
    WeekPlan,
    DayHealthReport,
    WeekHealthReport,
)


class HealthAgent:
    """
    Evaluates nutrition of a WeekPlan against user calorie/macro goals.
    """

    def _score_day(self, report: DayHealthReport, profile: UserHealthProfile) -> DayHealthReport:
        # simple scoring: penalty proportional to absolute percentage deviation
        flags: List[str] = []

        def pct_delta(actual: float, target: float) -> float:
            if target == 0:
                return 0.0
            return abs(actual - target) / target

        cal_pen = pct_delta(report.total_calories, profile.daily_calorie_target)
        prot_pen = pct_delta(report.total_protein_g, profile.protein_target_g)
        carb_pen = pct_delta(report.total_carbs_g, profile.carb_target_g)
        fat_pen = pct_delta(report.total_fat_g, profile.fat_target_g)

        raw_penalty = cal_pen + prot_pen + carb_pen + fat_pen
        score = max(0.0, 100.0 - raw_penalty * 25.0)  # tune factor

        if cal_pen > 0.2:
            flags.append("calories_far_from_target")
        if prot_pen > 0.2:
            flags.append("protein_far_from_target")
        if carb_pen > 0.2:
            flags.append("carbs_far_from_target")
        if fat_pen > 0.2:
            flags.append("fat_far_from_target")

        report.score = round(score, 1)
        report.flags = flags
        return report

    def evaluate_week(self, week_plan: WeekPlan, profile: UserHealthProfile) -> WeekHealthReport:
        daily_reports: List[DayHealthReport] = []

        for day in week_plan.days:
            total_cal = sum(m.macros_per_serving.calories for m in day.meals if m.macros_per_serving)
            total_prot = sum(m.macros_per_serving.protein_g for m in day.meals if m.macros_per_serving)
            total_carb = sum(m.macros_per_serving.carbs_g for m in day.meals if m.macros_per_serving)
            total_fat = sum(m.macros_per_serving.fat_g for m in day.meals if m.macros_per_serving)

            report = DayHealthReport(
                day_name=day.day_name,
                total_calories=round(total_cal, 1),
                total_protein_g=round(total_prot, 1),
                total_carbs_g=round(total_carb, 1),
                total_fat_g=round(total_fat, 1),
                calorie_delta=round(total_cal - profile.daily_calorie_target, 1),
                protein_delta=round(total_prot - profile.protein_target_g, 1),
                carb_delta=round(total_carb - profile.carb_target_g, 1),
                fat_delta=round(total_fat - profile.fat_target_g, 1),
                score=0.0,
                flags=[],
            )

            report = self._score_day(report, profile)
            daily_reports.append(report)

        avg_score = sum(r.score for r in daily_reports) / len(daily_reports)
        global_flags = []
        if avg_score < 70:
            global_flags.append("overall_plan_needs_adjustment")

        return WeekHealthReport(
            daily_reports=daily_reports,
            average_score=round(avg_score, 1),
            global_flags=global_flags,
        )

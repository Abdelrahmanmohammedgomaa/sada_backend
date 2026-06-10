from datetime import datetime
from collections import defaultdict


def calculate_average_score(scores):
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


def calculate_improvement_rate(scores):
    if len(scores) < 2 or scores[0] == 0:
        return 0.0
    return round(((scores[-1] - scores[0]) / scores[0]) * 100, 2)


def get_weekly_progress(activity):
    weekly = defaultdict(list)
    for item in activity:
        created_at = item.get("created_at")
        if isinstance(created_at, datetime):
            week_key = f"{created_at.isocalendar().year}-W{created_at.isocalendar().week}"
            weekly[week_key].append(item.get("score", 0))
    return {week: calculate_average_score(scores) for week, scores in weekly.items()}


def get_monthly_progress(activity):
    monthly = defaultdict(list)
    for item in activity:
        created_at = item.get("created_at")
        if isinstance(created_at, datetime):
            month_key = created_at.strftime("%Y-%m")
            monthly[month_key].append(item.get("score", 0))
    return {month: calculate_average_score(scores) for month, scores in monthly.items()}


def get_strongest_exercise(activity):
    if not activity:
        return None
    return max(activity, key=lambda item: item.get("score", 0)).get("exercise_id")


def get_weakest_exercise(activity):
    if not activity:
        return None
    return min(activity, key=lambda item: item.get("score", 0)).get("exercise_id")


class AnalyticsService:
    @staticmethod
    def get_child_analytics(db, child_id: int):
        _ = db
        _ = child_id
        return {
            "total_exercises": 0,
            "average_score": 0.0,
            "improvement_rate": 0.0,
        }

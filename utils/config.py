from typing import Dict, List


DB_TABLE_SCHEMAS: Dict[str, List[str]] = {
    "exercise": [
        "exercise_id", "name", "body_part_target", "video_url", "description",
        "difficulty_level", "equipment_required", "category",
        "created_at", "updated_at",
    ],
    "food": [
        "food_id", "name", "brand",
        "calories_100g", "protein_100g", "carbs_100g", "fat_100g",
        "nutriscore", "category_ref",
        "fiber_g", "sugar_g", "sodium_mg", "cholesterol_mg",
        "created_at", "updated_at",
    ],
    "user": [
        "user_id", "email", "password_hash",
        "first_name", "last_name", "birth_date", "gender_code",
        "created_at", "is_active", "role_code",
    ],
    "user_profile": [
        "profile_id", "user_id",
        "height_cm", "current_weight_kg", "activity_level_ref", "health_goal_id",
        "allergies_json", "preferences_json", "updated_at",
    ],
    "user_metrics": [
        "metric_id", "user_id", "recorded_date",
        "weight_kg", "body_fat_percentage", "steps", "calories_burned",
        "heart_rate_avg", "heart_rate_max", "sleep_hours", "created_at",
    ],
    "activity_type": [
        "activity_id", "name", "met_value", "icon_url",
    ],
    "workout_session": [
        "session_id", "user_id", "activity_id",
        "start_time", "duration_minutes", "calories_burned", "distance_km", "notes",
    ],
    "session_detail": [
        "detail_id", "session_id", "exercise_id",
        "sets", "reps", "weight_kg",
    ],
}
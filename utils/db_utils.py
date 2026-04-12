"""Database utility functions for ETL pipelines"""
import os
from typing import Dict, List


def get_db_config() -> dict:
    """Get database configuration from environment"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "healthai_db"),
        "user": os.getenv("DB_USER", "healthai"),
        "password": os.getenv("DB_PASSWORD", "password"),
    }

DB_TABLE_SCHEMAS: Dict[str, List[str]] = {
    # Exercise / workout tables
    "exercise": [
        "exercise_id", "name", "body_part_target", "video_url", "description",
        "difficulty_level", "equipment_required", "category",
    ],
    # Food / nutrition
    "ingredient": [
        "ingredient_id", "name", "usda_name",
        "calories_g", "fat_g", "nutriscore", "category",
        "fiber_g", "sugar_g", "sodium_mg", "cholesterol_mg",
        "protein_g", "carbs_g",
    ],
}
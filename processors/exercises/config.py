"""
Exercise pipeline configuration
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "exercises"
PROCESSED_DIR = DATA_DIR / "processed" / "exercises"

# Source URLs
EXERCISE_URLS = [
    "https://raw.githubusercontent.com/ExerciseDB/exercisedb-api/main/exercises.json",
    "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
]

# Local file
LOCAL_FILE = RAW_DIR / "exercises.json"

# Create directories
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

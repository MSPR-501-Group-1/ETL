from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent

# Data directories
RAW_DIR = ROOT_DIR / "data" / "raw" / "exercises"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "exercises"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Source URLs
URLS = [
    "https://raw.githubusercontent.com/ExerciseDB/exercisedb-api/main/exercises.json",
    "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
]

# Local file
LOCAL_FILE = RAW_DIR / "exercises.json"

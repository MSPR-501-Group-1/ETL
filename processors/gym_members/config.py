"""
Gym Members pipeline configuration
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "gym_members"
PROCESSED_DIR = DATA_DIR / "processed" / "gym_members"

# Kaggle dataset
KAGGLE_DATASET = "valakhorasani/gym-members-exercise-dataset"
LOCAL_FILE = RAW_DIR / "gym_members.csv"

# Create directories
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

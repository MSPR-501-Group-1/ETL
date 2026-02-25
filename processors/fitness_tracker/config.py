"""
Fitness Tracker pipeline configuration
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "fitness_tracker"
PROCESSED_DIR = DATA_DIR / "processed" / "fitness_tracker"

# Kaggle dataset
KAGGLE_DATASET = "nadeemajeedch/fitness-tracker-dataset"
LOCAL_FILE = RAW_DIR / "fitness_tracker.csv"

# Create directories
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

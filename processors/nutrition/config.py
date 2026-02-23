"""
Nutrition pipeline configuration
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "nutrition"
PROCESSED_DIR = DATA_DIR / "processed" / "nutrition"

# Kaggle dataset
KAGGLE_DATASET = "adilshamim8/daily-food-and-nutrition-dataset"
LOCAL_FILE = RAW_DIR / "food_nutrition.csv"

# Create directories
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

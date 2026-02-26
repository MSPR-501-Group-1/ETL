"""
Nutrition pipeline configuration
"""
from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).parent.parent.parent

# Data directories
RAW_DIR = ROOT_DIR / "data" / "raw" / "nutrition"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "nutrition"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle dataset
KAGGLE_DATASET = "adilshamim8/daily-food-and-nutrition-dataset"
DATASET_FILENAME = "Nutrition_Dataset.zip"

# Local paths
LOCAL_ZIP = RAW_DIR / DATASET_FILENAME
LOCAL_FILE = RAW_DIR / "Nutrition_Dataset.csv"

# Output paths
OUTPUT_PARQUET = PROCESSED_DIR / "nutrition_processed.parquet"
OUTPUT_CSV = PROCESSED_DIR / "Nutrition_processed.csv"

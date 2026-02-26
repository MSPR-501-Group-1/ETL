"""
Configuration for nutritional-values processor
Kaggle dataset: trolukovich/nutritional-values-for-common-foods-and-products
"""
from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).parent.parent.parent

# Data directories
RAW_DIR = ROOT_DIR / "data" / "raw" / "nutrition_values"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "nutrition_values"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle dataset configuration
KAGGLE_DATASET = "trolukovich/nutritional-values-for-common-foods-and-products"
DATASET_FILENAME = "Nutrition_values_Dataset.zip"

# Local paths
LOCAL_ZIP = RAW_DIR / DATASET_FILENAME
LOCAL_FILE = RAW_DIR / "Nutrition_values_Dataset.csv"  

# Output paths
OUTPUT_PARQUET = PROCESSED_DIR / "nutrition_values_processed.parquet"
OUTPUT_CSV = PROCESSED_DIR / "Nutrition_values_processed.csv"

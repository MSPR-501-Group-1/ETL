"""
Configuration for nutritional-values processor
Kaggle dataset: trolukovich/nutritional-values-for-common-foods-and-products
"""
from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).parent.parent.parent

# Data directories
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle dataset configuration
KAGGLE_DATASET = "trolukovich/nutritional-values-for-common-foods-and-products"
DATASET_FILENAME = "nutritional-values-for-common-foods-and-products.zip"

# Local paths
LOCAL_ZIP = RAW_DIR / DATASET_FILENAME
LOCAL_FILE = RAW_DIR / "nutrition-values.csv"  # Will be extracted from ZIP

# Output paths
OUTPUT_PARQUET = PROCESSED_DIR / "nutrition_values.parquet"
OUTPUT_CSV = PROCESSED_DIR / "nutrition_values_csv"

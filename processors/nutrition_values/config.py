import uuid
from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).parent.parent.parent

# Deterministic source ID for this dataset (used in etl_execution FK)
_NS_SOURCE = uuid.UUID('6ba7b820-9dad-11d1-80b4-00c04fd430c8')
SOURCE_ID = str(uuid.uuid5(_NS_SOURCE, "kaggle:trolukovich/nutritional-values-for-common-foods-and-products"))

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

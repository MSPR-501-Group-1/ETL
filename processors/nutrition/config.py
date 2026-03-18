from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).parent.parent.parent

# ── Source 1 : daily-food-and-nutrition-dataset ────────────────────────────────
RAW_DIR = ROOT_DIR / "data" / "raw" / "nutrition"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "nutrition"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

KAGGLE_DATASET = "adilshamim8/daily-food-and-nutrition-dataset"
DATASET_FILENAME = "Nutrition_Dataset.zip"

LOCAL_ZIP = RAW_DIR / DATASET_FILENAME
LOCAL_FILE = RAW_DIR / "Nutrition_Dataset.csv"

# ── Source 2 : nutritional-values-for-common-foods-and-products ────────────────
RAW_DIR_2 = ROOT_DIR / "data" / "raw" / "nutrition_values"
RAW_DIR_2.mkdir(parents=True, exist_ok=True)

KAGGLE_DATASET_2 = "trolukovich/nutritional-values-for-common-foods-and-products"
DATASET_FILENAME_2 = "Nutrition_values_Dataset.zip"

LOCAL_ZIP_2 = RAW_DIR_2 / DATASET_FILENAME_2
LOCAL_FILE_2 = RAW_DIR_2 / "Nutrition_values_Dataset.csv"

# Output paths

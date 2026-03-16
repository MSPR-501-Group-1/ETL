from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent

# Data directories
RAW_DIR = ROOT_DIR / "data" / "raw" / "fitness_tracker"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "fitness_tracker"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle dataset
KAGGLE_DATASET = "nadeemajeedch/fitness-tracker-dataset"
DATASET_FILENAME = "Fitness_Tracker_Dataset.zip"

# Local paths
LOCAL_ZIP = RAW_DIR / DATASET_FILENAME
LOCAL_FILE = RAW_DIR / "Fitness_Tracker_Dataset.csv"

# Output paths
OUTPUT_PARQUET = PROCESSED_DIR / "fitness_tracker_processed.parquet"
OUTPUT_CSV = PROCESSED_DIR / "fitness_tracker_processed.csv"
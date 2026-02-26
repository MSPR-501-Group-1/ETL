"""
Gym Members pipeline configuration
"""
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent

# Data directories
RAW_DIR = ROOT_DIR / "data" / "raw" / "gym_members"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "gym_members"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle dataset
KAGGLE_DATASET = "valakhorasani/gym-members-exercise-dataset"
DATASET_FILENAME =  "Gym_members_Dataset.zip"

# Local paths
LOCAL_ZIP = RAW_DIR / DATASET_FILENAME
LOCAL_FILE = RAW_DIR / "Gym_members_Dataset.csv"

# Output paths
OUTPUT_PARQUET = PROCESSED_DIR / "gym_members_processed.parquet"
OUTPUT_CSV = PROCESSED_DIR / "Gym_members_processed.csv"



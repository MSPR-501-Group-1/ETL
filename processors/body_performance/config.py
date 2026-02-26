"""
Body Performance pipeline configuration
"""
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent

# Data directories
RAW_DIR = ROOT_DIR / "data" / "raw" / "body_performance"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "body_performance"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle dataset
KAGGLE_DATASET = "kukuroo3/body-performance-data"
DATASET_FILENAME = RAW_DIR / "Body_performance_Dataset.zip"

# Local paths
LOCAL_ZIP = RAW_DIR / DATASET_FILENAME
LOCAL_FILE = RAW_DIR / "Body_performance_Dataset.csv"

# Output paths
OUTPUT_PARQUET = PROCESSED_DIR / "Body_performance_processed.parquet"
OUTPUT_CSV = PROCESSED_DIR / "Body_performance_processed.csv"

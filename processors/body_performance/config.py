"""
Body Performance pipeline configuration
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "body_performance"
PROCESSED_DIR = DATA_DIR / "processed" / "body_performance"

# Kaggle dataset
KAGGLE_DATASET = "kukuroo3/body-performance-data"
LOCAL_FILE = RAW_DIR / "bodyPerformance.csv"

# Create directories
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

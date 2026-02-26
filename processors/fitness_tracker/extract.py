"""
Extract fitness tracker data from Kaggle
"""
import sys
from pathlib import Path
from processors.fitness_tracker.config import KAGGLE_DATASET, LOCAL_FILE, RAW_DIR, LOCAL_ZIP
from utils.extract import download_kaggle

download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)

if __name__ == "__main__":
    success = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)
    sys.exit(0 if success else 1)

"""
Extract nutritional values data from Kaggle
Dataset: trolukovich/nutritional-values-for-common-foods-and-products
"""
import sys
from pathlib import Path
from utils.kaggle.extract import check_kaggle_credentials, download_kaggle, extract_zip_file
from processors.nutrition_values.config import (
    KAGGLE_DATASET, RAW_DIR, LOCAL_ZIP, LOCAL_FILE
)


download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)

if __name__ == "__main__":
    result = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)
    
    if result:
        print("\n" + "=" * 60)
        print("🎉 EXTRACTION COMPLETED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ EXTRACTION FAILED")
        print("=" * 60)
        sys.exit(1)

"""
Extract nutrition data from Kaggle
"""
from pathlib import Path
from utils.kaggle.extract import download_kaggle
from processors.nutrition.config import KAGGLE_DATASET, RAW_DIR, LOCAL_FILE, LOCAL_ZIP

download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)

def get_nutrition_stats(file_path: str) -> dict:
    """Get basic stats from CSV"""
    import pandas as pd
    
    try:
        df = pd.read_csv(file_path, nrows=5)
        
        stats = {
            "columns": list(df.columns),
            "sample_count": 5,
            "first_row": df.iloc[0].to_dict()
        }
        
        return stats
    except Exception as e:
        print(f"⚠️  Could not read stats: {e}")
        return {}

if __name__ == "__main__":
    file_path = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)
    
    if file_path:
        print("\n" + "=" * 60)
        print("📊 DATA PREVIEW")
        print("=" * 60)
        
        stats = get_nutrition_stats(file_path)
        if stats:
            print(f"Columns: {stats.get('columns', [])}")

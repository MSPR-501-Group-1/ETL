"""
Extract nutrition data from Kaggle
"""
import os
import subprocess
from pathlib import Path
from processors.nutrition.config import KAGGLE_DATASET, RAW_DIR, LOCAL_FILE

def download_nutrition(force_download: bool = False) -> str:
    """Download nutrition dataset from Kaggle"""
    print("⏳ Extracting nutrition data...")
    
    # Check if file exists
    if LOCAL_FILE.exists() and not force_download:
        if not os.isatty(0):  # Non-interactive (Docker)
            print("✅ Extract completed (from cache)")
            return str(LOCAL_FILE)
        
        response = input("   Download again? (y/N): ").strip().lower()
        if response != 'y':
            print("✅ Extract completed (from cache)")
            return str(LOCAL_FILE)
    
    # Check Kaggle credentials
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        print("❌ FAILED: Kaggle credentials not found")
        
        # Check env variables
        if not (os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")):
            raise FileNotFoundError("Kaggle credentials missing")
    
    try:
        # Download using kaggle CLI
        cmd = [
            "kaggle", "datasets", "download",
            "-d", KAGGLE_DATASET,
            "-p", str(RAW_DIR),
            "--unzip"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Find downloaded CSV
        csv_files = list(RAW_DIR.glob("*.csv"))
        if not csv_files:
            print("❌ FAILED: No CSV found after download")
            return None
        
        downloaded_file = csv_files[0]
        
        # Rename to standard name if needed
        if downloaded_file != LOCAL_FILE:
            downloaded_file.rename(LOCAL_FILE)
        
        print("✅ Extract completed")
        return str(LOCAL_FILE)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: Kaggle download error - {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return None

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
    file_path = download_nutrition()
    
    if file_path:
        print("\n" + "=" * 60)
        print("📊 DATA PREVIEW")
        print("=" * 60)
        
        stats = get_nutrition_stats(file_path)
        if stats:
            print(f"Columns: {stats.get('columns', [])}")

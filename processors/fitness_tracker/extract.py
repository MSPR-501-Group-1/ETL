"""
Extract fitness tracker data from Kaggle
"""
import os
import subprocess
import sys
from pathlib import Path
from processors.fitness_tracker.config import KAGGLE_DATASET, LOCAL_FILE, RAW_DIR

def check_kaggle_credentials():
    """Check if Kaggle credentials are configured"""
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    
    if not kaggle_json.exists():
        # Check environment variables as fallback
        if not (os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")):
            print("❌ FAILED: Kaggle credentials not found")
            return False
    
    return True

def download_fitness_tracker():
    """Download fitness tracker dataset from Kaggle"""
    print("⏳ Extracting fitness tracker data...")
    
    # Check if file exists
    if LOCAL_FILE.exists():
        if not os.isatty(0):  # Non-interactive (Docker)
            print("✅ Extract completed (from cache)")
            return True
        
        response = input("   Re-download? (y/N): ").strip().lower()
        if response != 'y':
            print("✅ Extract completed (from cache)")
            return True
    
    # Check credentials
    if not check_kaggle_credentials():
        return False
    
    # Download
    try:
        cmd = [
            "kaggle", "datasets", "download",
            "-d", KAGGLE_DATASET,
            "-p", str(RAW_DIR),
            "--unzip"
        ]
        
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Find downloaded CSV and rename if needed
        csv_files = list(RAW_DIR.glob("*.csv"))
        if not csv_files:
            print("❌ FAILED: No CSV found after download")
            return False
        
        downloaded_file = csv_files[0]
        
        # Rename to standard name if needed
        if downloaded_file != LOCAL_FILE:
            downloaded_file.rename(LOCAL_FILE)
        
        print("✅ Extract completed")
        return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: Download error - {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ FAILED: Kaggle CLI not found")
        return False

if __name__ == "__main__":
    success = download_fitness_tracker()
    sys.exit(0 if success else 1)

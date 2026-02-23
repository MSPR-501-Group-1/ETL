"""
Extract nutritional values data from Kaggle
Dataset: trolukovich/nutritional-values-for-common-foods-and-products
"""
import os
import sys
import subprocess
import zipfile
from pathlib import Path
from processors.nutrition_values.config import (
    KAGGLE_DATASET, RAW_DIR, LOCAL_ZIP, LOCAL_FILE
)

def check_kaggle_credentials():
    """Check if Kaggle credentials are configured"""
    kaggle_json_home = Path.home() / ".kaggle" / "kaggle.json"
    kaggle_json_local = Path("kaggle.json")
    
    has_env = os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")
    has_file = kaggle_json_home.exists() or kaggle_json_local.exists()
    
    if not (has_env or has_file):
        print("❌ Kaggle credentials not found!")
        print("\n📝 Configuration required:")
        print("   1. Download kaggle.json from: https://www.kaggle.com/account")
        print("   2. Place it in: ~/.kaggle/kaggle.json")
        print("   OR set KAGGLE_USERNAME and KAGGLE_KEY environment variables")
        return False
    
    return True

def extract_zip_file():
    """Extract CSV from downloaded ZIP file"""
    if not LOCAL_ZIP.exists():
        print(f"❌ ZIP file not found: {LOCAL_ZIP}")
        return False
    
    print(f"📦 Extracting ZIP file...")
    
    try:
        with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
            # List files in ZIP
            file_list = zip_ref.namelist()
            print(f"   Files in ZIP: {file_list}")
            
            # Find CSV file (usually the main data file)
            csv_files = [f for f in file_list if f.endswith('.csv')]
            
            if not csv_files:
                print("❌ No CSV file found in ZIP")
                return False
            
            # Extract first CSV file
            main_csv = csv_files[0]
            print(f"   Extracting: {main_csv}")
            
            # Extract to RAW_DIR
            zip_ref.extract(main_csv, RAW_DIR)
            
            # Rename to expected filename if different
            extracted_path = RAW_DIR / main_csv
            if extracted_path != LOCAL_FILE:
                extracted_path.rename(LOCAL_FILE)
                print(f"   Renamed to: {LOCAL_FILE.name}")
            
            print(f"✅ Extraction completed: {LOCAL_FILE}")
            return True
            
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return False

def download_nutrition_values():
    """Download nutritional values dataset from Kaggle"""
    
    print("=" * 60)
    print("📥 EXTRACT NUTRITION VALUES DATA")
    print("=" * 60)
    print(f"Source: Kaggle - {KAGGLE_DATASET}")
    print(f"Target: {RAW_DIR}")
    print()
    
    # Check if already downloaded
    if LOCAL_FILE.exists():
        file_size = LOCAL_FILE.stat().st_size / (1024 * 1024)  # MB
        
        # Non-interactive mode check (Docker)
        if not sys.stdin or not os.isatty(0):
            print(f"✅ File already exists: {LOCAL_FILE.name} ({file_size:.2f} MB)")
            print("   Skipping download (non-interactive mode)")
            return str(LOCAL_FILE)
        
        # Interactive mode: ask user
        response = input(f"⚠️  File already exists ({file_size:.2f} MB). Re-download? (y/N): ")
        if response.lower() != 'y':
            print("✅ Using existing file")
            return str(LOCAL_FILE)
        
        print("🔄 Re-downloading...")
        LOCAL_FILE.unlink()
        if LOCAL_ZIP.exists():
            LOCAL_ZIP.unlink()
    
    # Check credentials
    if not check_kaggle_credentials():
        return None
    
    # Download using Kaggle CLI
    print(f"📥 Downloading from Kaggle...")
    print(f"   Dataset: {KAGGLE_DATASET}")
    
    try:
        # Run kaggle datasets download command
        result = subprocess.run(
            [
                "kaggle", "datasets", "download",
                "-d", KAGGLE_DATASET,
                "-p", str(RAW_DIR),
                "--unzip"  # Auto-unzip option
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Download completed")
        print(result.stdout)
        
        # Check if file was extracted automatically
        if not LOCAL_FILE.exists():
            # Try to find and rename the extracted CSV
            csv_files = list(RAW_DIR.glob("*.csv"))
            if csv_files:
                csv_files[0].rename(LOCAL_FILE)
                print(f"✅ Renamed to: {LOCAL_FILE.name}")
            else:
                print("⚠️  CSV not found after extraction, checking ZIP...")
                if not extract_zip_file():
                    return None
        
        # Verify file
        if LOCAL_FILE.exists():
            file_size = LOCAL_FILE.stat().st_size / (1024 * 1024)
            print(f"\n✅ Extraction successful!")
            print(f"   File: {LOCAL_FILE}")
            print(f"   Size: {file_size:.2f} MB")
            return str(LOCAL_FILE)
        else:
            print("❌ File not found after extraction")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        print(f"   stderr: {e.stderr}")
        return None
        
    except FileNotFoundError:
        print("❌ Kaggle CLI not found!")
        print("\n📝 Installation required:")
        print("   pip install kaggle")
        return None

if __name__ == "__main__":
    result = download_nutrition_values()
    
    if result:
        print("\n" + "=" * 60)
        print("🎉 EXTRACTION COMPLETED")
        print("=" * 60)
        print(f"✅ Data ready: {result}")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ EXTRACTION FAILED")
        print("=" * 60)
        sys.exit(1)

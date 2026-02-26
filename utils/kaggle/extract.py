# Common methods for extracting data
import os
import subprocess
import zipfile

from pathlib import Path

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


def extract_zip_file(LOCAL_ZIP: Path, LOCAL_FILE: Path, RAW_DIR: Path) -> bool:
    """Extract CSV from downloaded ZIP file"""
    if not LOCAL_ZIP.exists():
        print(f"❌ FAILED: ZIP file not found")
        return False
    
    try:
        with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
            # List files in ZIP
            file_list = zip_ref.namelist()
            
            # Find CSV file (usually the main data file)
            csv_files = [f for f in file_list if f.endswith('.csv')]
            
            if not csv_files:
                print("❌ FAILED: No CSV file found in ZIP")
                return False
            
            # Extract first CSV file
            main_csv = csv_files[0]
            
            # Extract to RAW_DIR
            zip_ref.extract(main_csv, RAW_DIR)
            
            # Rename to expected filename if different
            extracted_path = RAW_DIR / main_csv
            if extracted_path != LOCAL_FILE:
                extracted_path.rename(LOCAL_FILE)
            
            return True
            
    except Exception as e:
        print(f"❌ FAILED: Extraction error - {e}")
        return False
    
def download_kaggle(LOCAL_ZIP: Path, LOCAL_FILE: Path, RAW_DIR: Path, KAGGLE_DATASET: str) -> bool:
    """Download nutritional values dataset from Kaggle"""
    
    print("⏳ Extracting nutrition values data...")
    
    # Check if already downloaded
    if LOCAL_FILE.exists():
        if not os.isatty(0):  # Non-interactive mode (Docker)
            print("✅ Extract completed (from cache)")
            return str(LOCAL_FILE)
        
        # Interactive mode: ask user
        file_size = LOCAL_FILE.stat().st_size / (1024 * 1024)  # MB
        response = input(f"   File exists ({file_size:.2f} MB). Re-download? (y/N): ")
        if response.lower() != 'y':
            print("✅ Extract completed (from cache)")
            return str(LOCAL_FILE)
        
        LOCAL_FILE.unlink()
        if LOCAL_ZIP.exists():
            LOCAL_ZIP.unlink()
    
    # Check credentials
    if not check_kaggle_credentials():
        return None
    
    # Download using Kaggle CLI
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
        
        # Check if file was extracted automatically
        if not LOCAL_FILE.exists():
            # Try to find and rename the extracted CSV
            csv_files = list(RAW_DIR.glob("*.csv"))
            if csv_files:
                csv_files[0].rename(LOCAL_FILE)
            else:
                if not extract_zip_file():
                    return None
        
        # Verify file
        if LOCAL_FILE.exists():
            print("✅ Extract completed")
            return str(LOCAL_FILE)
        else:
            print("❌ FAILED: File not found after extraction")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: Download error - {e.stderr}")
        return None
        
    except FileNotFoundError:
        print("❌ FAILED: Kaggle CLI not found")
        return None
"""
Verification script for Nutrition pipeline setup
"""
import os
import sys
from pathlib import Path

def check_kaggle_credentials():
    """Check if Kaggle credentials are configured"""
    kaggle_json_home = Path.home() / ".kaggle" / "kaggle.json"
    kaggle_json_local = Path("kaggle.json")
    
    has_env = os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")
    has_file = kaggle_json_home.exists() or kaggle_json_local.exists()
    
    if has_env:
        print("✅ Kaggle credentials found in environment variables")
        return True
    elif has_file:
        file_path = kaggle_json_home if kaggle_json_home.exists() else kaggle_json_local
        print(f"✅ Kaggle credentials found: {file_path}")
        return True
    else:
        print("❌ Kaggle credentials NOT found")
        print("\n📝 Configuration required:")
        print("   Option 1: Place kaggle.json in ~/.kaggle/kaggle.json")
        print("   Option 2: Set KAGGLE_USERNAME and KAGGLE_KEY env vars")
        print("\n   Download kaggle.json from: https://www.kaggle.com/account")
        return False

def check_directories():
    """Verify required directories exist"""
    dirs = ["data/raw", "data/processed"]
    all_ok = True
    
    for dir_path in dirs:
        if Path(dir_path).exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"⚠️  Directory missing: {dir_path} (will be created)")
            all_ok = False
    
    return all_ok

def check_files():
    """Check if nutrition processor files exist"""
    files = [
        "processors/nutrition/__init__.py",
        "processors/nutrition/config.py",
        "processors/nutrition/extract.py",
        "processors/nutrition/transform.py",
        "processors/nutrition/load.py",
        "processors/nutrition/pipeline.py"
    ]
    
    all_exist = True
    for file_path in files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} NOT FOUND")
            all_exist = False
    
    return all_exist

def main():
    print("=" * 70)
    print("🔍 NUTRITION PIPELINE VERIFICATION")
    print("=" * 70)
    
    print("\n📦 Checking processor files...")
    files_ok = check_files()
    
    print("\n📁 Checking directories...")
    dirs_ok = check_directories()
    
    print("\n🔑 Checking Kaggle credentials...")
    kaggle_ok = check_kaggle_credentials()
    
    print("\n" + "=" * 70)
    
    if files_ok and kaggle_ok:
        print("✅ READY TO RUN")
        print("\n� Lancer avec Docker (RECOMMANDÉ - évite les problèmes Java):")
        print("   docker-compose run --rm etl python main.py --pipeline nutrition")
        print("\n   Les deux pipelines:")
        print("   docker-compose run --rm etl python main.py --pipeline all")
        print("\n⚠️  Note: Docker utilise Java 17 (compatible PySpark)")
        print("   Exécution locale déconseillée si Java 25+ installé")
        return 0
    else:
        print("❌ CONFIGURATION INCOMPLETE")
        if not kaggle_ok:
            print("\n⚠️  Missing Kaggle credentials - see instructions above")
        if not files_ok:
            print("⚠️  Missing processor files")
        return 1

if __name__ == "__main__":
    sys.exit(main())

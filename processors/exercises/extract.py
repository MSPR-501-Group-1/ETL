"""
Extract ExerciseDB data from GitHub
"""
import requests
import json
import os
from pathlib import Path
from processors.exercises.config import EXERCISE_URLS, LOCAL_FILE

def download_exercises(force_download: bool = False) -> dict:
    """Download exercises data from GitHub URLs"""

    print("🏋️  ExerciseDB - Extract raw data")
    print("=" * 60)
    
    # Check if file already exists
    if LOCAL_FILE.exists() and not force_download:
        print(f"✅ File exists: {LOCAL_FILE}")
        
        # Auto-load in non-interactive mode (Docker)
        if not os.isatty(0):  # Non-interactive (Docker)
            print("📖 Reading local file (non-interactive mode)...")
            with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ {len(data)} exercises loaded from cache")
            return data
        
        # Ask confirmation in interactive mode
        response = input("   Download again? (y/N): ").strip().lower()
        if response != 'y':
            print("📖 Reading local file...")
            with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ {len(data)} exercises loaded from cache")
            return data
    
    # Try downloading from sources
    for i, url in enumerate(EXERCISE_URLS, 1):
        print(f"\n⬇️  Attempt {i}/{len(EXERCISE_URLS)}")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                print(f"⚠️  Unexpected format, trying next...")
                continue
            
            print(f"💾 Saving to: {LOCAL_FILE}")
            with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {len(data)} exercises downloaded!")
            
            if data:
                print(f"\n📊 Data preview:")
                print(f"   Count: {len(data)}")
                print(f"   Columns: {list(data[0].keys())}")
                print(f"\n   First exercise:")
                for key, value in list(data[0].items())[:5]:
                    print(f"      {key}: {value}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            continue
    
    print("\n❌ Download failed from all sources")
    return None

def get_exercises_stats(data: list) -> dict:
    """Generate basic statistics"""
    if not data:
        return {}
    
    stats = {
        "total": len(data),
        "columns": list(data[0].keys()) if data else [],
        "unique_body_parts": len(set(ex.get("bodyPart", "") for ex in data)),
        "unique_equipment": len(set(ex.get("equipment", "") for ex in data)),
        "unique_targets": len(set(ex.get("target", "") for ex in data))
    }
    
    return stats

if __name__ == "__main__":
    data = download_exercises()
    
    if data:
        print("\n" + "=" * 60)
        print("📊 STATISTICS")
        print("=" * 60)
        
        stats = get_exercises_stats(data)
        for key, value in stats.items():
            print(f"{key}: {value}")

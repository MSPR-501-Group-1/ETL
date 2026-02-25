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

    print("⏳ Extracting exercises data...")
    
    # Check if file already exists
    if LOCAL_FILE.exists() and not force_download:
        # Auto-load in non-interactive mode (Docker)
        if not os.isatty(0):  # Non-interactive (Docker)
            with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("✅ Extract completed (from cache)")
            return data
        
        # Ask confirmation in interactive mode
        response = input("   Download again? (y/N): ").strip().lower()
        if response != 'y':
            with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("✅ Extract completed (from cache)")
            return data
    
    # Try downloading from sources
    for i, url in enumerate(EXERCISE_URLS, 1):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                continue
            
            with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✅ Extract completed")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED source {i}: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"❌ FAILED source {i}: JSON parsing error - {e}")
            continue
    
    print("❌ FAILED: All sources failed")
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

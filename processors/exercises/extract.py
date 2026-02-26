"""
Extract ExerciseDB data from GitHub
"""
from pathlib import Path
from processors.exercises.config import LOCAL_FILE, URLS
from utils.github.extract import download_github

download_github(LOCAL_FILE, URLS, force_download=True)

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
    data = download_github(LOCAL_FILE, URLS, force_download=True)
    
    if data:
        print("\n" + "=" * 60)
        print("📊 STATISTICS")
        print("=" * 60)
        
        stats = get_exercises_stats(data)
        for key, value in stats.items():
            print(f"{key}: {value}")

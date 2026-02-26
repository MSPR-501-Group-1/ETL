import json
import os
from pathlib import Path

import requests

def download_github(LOCAL_FILE: Path, URLS: list = None, force_download: bool = False) -> dict:
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
    for i, url in enumerate(URLS, 1):
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
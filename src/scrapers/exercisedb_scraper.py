"""
Scraper to fetch exercise data from ExerciseDB (GitHub)
Source: https://github.com/yuhonas/free-exercise-db

This module automatically downloads a list of exercises
with their characteristics (muscles, equipment, instructions, etc.)
"""

import requests
import time
from pathlib import Path
from typing import List, Dict, Optional
from config.settings import RAW_DATA_DIR, SCRAPING_CONFIG
from src.utils.logger import setup_logger
from src.utils.file_handler import save_to_json, generate_filename


class ExerciseDBScraper:
    """
    Main class to fetch exercises from ExerciseDB
    
    Process:
    1. Connect to GitHub URL containing JSON data
    2. Download complete exercise list
    3. Extract metadata (categories, equipment, etc.)
    4. Save to local JSON file
    """
    
    BASE_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
    
    def __init__(self):
        """
        Initialize the scraper
        
        Creates:
        - Logger for execution tracking
        - HTTP session for web requests
        - User-Agent configuration
        """
        self.logger = setup_logger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': SCRAPING_CONFIG['user_agent']
        })
        
    def fetch_exercises(self) -> Optional[List[Dict]]:
        """
        Download all exercises from GitHub URL
        
        Process:
        1. Make HTTP GET request to URL
        2. Verify request succeeded (code 200)
        3. Convert JSON response to Python list
        
        Returns:
            List[Dict]: List of dictionaries containing exercises
            None: If download fails
        """
        self.logger.info(f"Downloading exercises from {self.BASE_URL}")
        
        try:
            response = self.session.get(
                self.BASE_URL,
                timeout=SCRAPING_CONFIG['timeout']
            )
            response.raise_for_status()
            exercises = response.json()
            self.logger.info(f"Success: {len(exercises)} exercises downloaded")
            return exercises
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Download failed: {e}")
            return None
    
    def fetch_exercise_categories(self, exercises: List[Dict]) -> Dict[str, List[str]]:
        """
        Extract unique categories from exercise list
        
        Creates lists of:
        - Muscle groups (bodyParts): biceps, triceps, abs, etc.
        - Equipment: dumbbells, barbells, bodyweight, etc.
        - Exercise types (targets): cardio, strength, stretching, etc.
        
        Args:
            exercises: List of downloaded exercises
            
        Returns:
            Dict: Dictionary with 3 keys (bodyParts, equipment, targets)
                  each containing sorted list of unique values
        """
        categories = {
            'bodyParts': set(),
            'equipment': set(),
            'targets': set()
        }
        
        for exercise in exercises:
            if 'primaryMuscles' in exercise and exercise['primaryMuscles']:
                categories['bodyParts'].update(exercise['primaryMuscles'])
            
            if 'equipment' in exercise and exercise['equipment']:
                categories['equipment'].add(exercise['equipment'])
            
            if 'category' in exercise and exercise['category']:
                categories['targets'].add(exercise['category'])
        
        return {key: sorted([v for v in values if v is not None]) for key, values in categories.items()}
    
    def save_data(self, exercises: List[Dict], filename: Optional[str] = None) -> Path:
        """
        Save data to JSON file
        
        Creates JSON file with all fetched data.
        Filename includes timestamp for version tracking.
        
        Args:
            exercises: Data to save (dict with metadata + exercises)
            filename: Filename (optional, auto-generated if not provided)
            
        Returns:
            Path: Full path to created file
        """
        if filename is None:
            filename = generate_filename('exercisedb_raw')
        
        filepath = RAW_DATA_DIR / filename
        save_to_json(exercises, filepath)
        self.logger.info(f"Saved {len(exercises)} exercises to {filepath}")
        return filepath
    
    def run(self) -> Optional[Path]:
        """
        Execute complete scraping pipeline
        
        Steps:
        1. Download exercises from URL
        2. Extract metadata (categories)
        3. Structure data with metadata
        4. Save to JSON file
        
        Returns:
            Path: Path to created file
            None: If error occurred
        """
        self.logger.info("Starting ExerciseDB scraping pipeline")
        
        exercises = self.fetch_exercises()
        if exercises is None:
            self.logger.error("Scraping failed - no data retrieved")
            return None
        
        categories = self.fetch_exercise_categories(exercises)
        self.logger.info(f"Categories found: {categories}")
        
        data = {
            'metadata': {
                'source': 'ExerciseDB',
                'url': self.BASE_URL,
                'total_exercises': len(exercises),
                'categories': categories,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'exercises': exercises
        }
        
        filepath = self.save_data(data)
        self.logger.info("ExerciseDB scraping completed successfully")
        return filepath


if __name__ == "__main__":
    # Test the scraper
    scraper = ExerciseDBScraper()
    result = scraper.run()
    
    if result:
        print(f"✅ Data successfully saved to: {result}")
    else:
        print("❌ Scraping failed")

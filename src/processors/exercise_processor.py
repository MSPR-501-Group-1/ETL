"""
Processor to clean and transform ExerciseDB exercise data

Applies following transformations:
1. Data structure validation
2. Field cleaning (normalization, null handling)
3. Data enrichment (score calculation, categorization)
4. Deduplication and consistency
5. Export to usable format
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import setup_logger
from src.utils.file_handler import save_to_json, save_to_csv, load_from_json
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR


class ExerciseProcessor:
    """
    Processor to clean and transform exercise data
    
    Transformation pipeline:
    1. Load raw data
    2. Structure validation
    3. Cleaning and normalization
    4. Enrichment
    5. Export clean data
    """
    
    def __init__(self):
        """Initialize processor and logging system"""
        self.logger = setup_logger(self.__class__.__name__)
        self.stats = {
            'total_exercises': 0,
            'valid_exercises': 0,
            'invalid_exercises': 0,
            'duplicates_removed': 0,
            'fields_cleaned': 0
        }
    
    def load_raw_data(self, filepath: Path) -> Tuple[Dict, pd.DataFrame]:
        """
        Load raw data from JSON file
        
        Args:
            filepath: Path to raw JSON file
            
        Returns:
            Tuple containing (metadata, exercises DataFrame)
        """
        self.logger.info(f"Loading data from {filepath}")
        
        raw_data = load_from_json(filepath)
        metadata = raw_data.get('metadata', {})
        exercises = raw_data.get('exercises', [])
        df = pd.DataFrame(exercises)
        
        self.stats['total_exercises'] = len(df)
        self.logger.info(f"{len(df)} exercises loaded")
        
        return metadata, df
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data structure and consistency
        
        Validation rules:
        - Required fields: name, id, category, equipment, primaryMuscles
        - Correct format for lists and strings
        - Consistent values (level, category, equipment in allowed lists)
        
        Args:
            df: Exercises DataFrame
            
        Returns:
            DataFrame with only valid exercises
        """
        self.logger.info("Validating data...")
        
        initial_count = len(df)
        required_fields = ['name', 'id', 'category', 'equipment', 'primaryMuscles']
        
        for field in required_fields:
            if field not in df.columns:
                self.logger.warning(f"Missing required field: {field}")
                df[field] = None
        
        mask = df['name'].notna() & df['id'].notna()
        df = df[mask].copy()
        
        for list_field in ['primaryMuscles', 'secondaryMuscles', 'instructions']:
            if list_field in df.columns:
                df[list_field] = df[list_field].apply(
                    lambda x: x if isinstance(x, list) else []
                )
        
        valid_levels = ['beginner', 'intermediate', 'expert']
        df['level'] = df['level'].apply(
            lambda x: x if x in valid_levels else 'intermediate'
        )
        
        valid_categories = [
            'cardio', 'olympic weightlifting', 'plyometrics',
            'powerlifting', 'strength', 'stretching', 'strongman'
        ]
        df['category'] = df['category'].apply(
            lambda x: x if x in valid_categories else 'strength'
        )
        
        self.stats['valid_exercises'] = len(df)
        self.stats['invalid_exercises'] = initial_count - len(df)
        
        self.logger.info(
            f"Validation complete: {self.stats['valid_exercises']} valid, "
            f"{self.stats['invalid_exercises']} rejected"
        )
        
        return df
    
    def clean_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize text fields
        
        Operations:
        - Trim whitespace
        - Normalize case
        - Remove unwanted special characters
        
        Args:
            df: Exercises DataFrame
            
        Returns:
            DataFrame with cleaned text fields
        """
        self.logger.info("Cleaning text fields...")
        
        text_fields = ['name', 'equipment', 'force', 'mechanic', 'category']
        
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].apply(
                    lambda x: x.strip().lower() if isinstance(x, str) else x
                )
                self.stats['fields_cleaned'] += 1
        
        return df
    
    def normalize_muscle_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize and enrich muscle groups
        
        Operations:
        - Standardize muscle names
        - Add 'all_muscles' column combining primary + secondary
        - Count targeted muscles
        
        Args:
            df: Exercises DataFrame
            
        Returns:
            Enriched DataFrame
        """
        self.logger.info("Normalizing muscle groups...")
        
        muscle_mapping = {
            'abs': 'abdominals',
            'quads': 'quadriceps',
            'lats': 'lats',
            'traps': 'trapezius',
        }
        
        def normalize_muscle_list(muscles):
            """Normalize muscle list"""
            if not isinstance(muscles, list):
                return []
            return [muscle_mapping.get(m.lower(), m.lower()) for m in muscles]
        
        df['primaryMuscles'] = df['primaryMuscles'].apply(normalize_muscle_list)
        df['secondaryMuscles'] = df['secondaryMuscles'].apply(normalize_muscle_list)
        
        df['all_muscles'] = df.apply(
            lambda row: list(set(row['primaryMuscles'] + row['secondaryMuscles'])),
            axis=1
        )
        
        df['muscle_count'] = df['all_muscles'].apply(len)
        
        df['exercise_type'] = df['muscle_count'].apply(
            lambda x: 'compound' if x > 2 else 'isolation'
        )
        
        return df
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich data with calculated fields
        
        Additions:
        - Numerical difficulty (1-3)
        - Complexity score based on instructions
        - Requires equipment (boolean)
        - Main movement category
        
        Args:
            df: Exercises DataFrame
            
        Returns:
            Enriched DataFrame
        """
        self.logger.info("Enriching data...")
        
        level_scores = {'beginner': 1, 'intermediate': 2, 'expert': 3}
        df['difficulty_score'] = df['level'].map(level_scores)
        
        df['instruction_count'] = df['instructions'].apply(len)
        df['complexity_score'] = df.apply(
            lambda row: row['difficulty_score'] + (row['instruction_count'] / 10),
            axis=1
        )
        
        df['requires_equipment'] = df['equipment'].apply(
            lambda x: x not in ['body only', 'none', None]
        )
        
        push_indicators = ['push', 'press', 'chest', 'triceps', 'shoulders']
        pull_indicators = ['pull', 'row', 'back', 'biceps', 'lats']
        
        def categorize_movement(row):
            """Categorize movement type"""
            name_lower = row['name'].lower() if isinstance(row['name'], str) else ''
            
            if any(word in name_lower for word in push_indicators):
                return 'push'
            elif any(word in name_lower for word in pull_indicators):
                return 'pull'
            elif row['category'] in ['cardio', 'stretching']:
                return row['category']
            else:
                return 'other'
        
        df['movement_type'] = df.apply(categorize_movement, axis=1)
        
        return df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate exercises
        
        Strategy:
        - Identify duplicates by 'id' or 'name'
        - Keep most complete version
        
        Args:
            df: Exercises DataFrame
            
        Returns:
            Deduplicated DataFrame
        """
        self.logger.info("Removing duplicates...")
        
        initial_count = len(df)
        df = df.drop_duplicates(subset=['id'], keep='first')
        df = df.drop_duplicates(subset=['name'], keep='first')
        
        self.stats['duplicates_removed'] = initial_count - len(df)
        self.logger.info(f"{self.stats['duplicates_removed']} duplicates removed")
        
        return df
    
    def add_metadata_columns(self, df: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        """
        Add metadata columns for traceability
        
        Args:
            df: Exercises DataFrame
            metadata: Metadata dictionary
            
        Returns:
            DataFrame with metadata
        """
        df['data_source'] = metadata.get('source', 'ExerciseDB')
        df['scraped_at'] = metadata.get('scraped_at', datetime.now().isoformat())
        df['processed_at'] = datetime.now().isoformat()
        
        return df
    
    def get_processing_stats(self) -> Dict:
        """
        Return processing statistics
        
        Returns:
            Statistics dictionary
        """
        return self.stats
    
    def export_processed_data(
        self,
        df: pd.DataFrame,
        metadata: Dict,
        output_format: str = 'both'
    ) -> Dict[str, Path]:
        """
        Export processed data to JSON and/or CSV
        
        Args:
            df: Processed exercises DataFrame
            metadata: Metadata to include
            output_format: 'json', 'csv' or 'both'
            
        Returns:
            Dictionary of created file paths
        """
        self.logger.info(f"Exporting data in {output_format} format...")
        
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exported_files = {}
        
        if output_format in ['json', 'both']:
            json_filename = f'exercises_processed_{timestamp}.json'
            json_filepath = PROCESSED_DATA_DIR / json_filename
            
            output_data = {
                'metadata': {
                    **metadata,
                    'processing_stats': self.stats,
                    'processed_at': datetime.now().isoformat(),
                    'total_processed_exercises': len(df)
                },
                'exercises': df.to_dict('records')
            }
            
            save_to_json(output_data, json_filepath)
            exported_files['json'] = json_filepath
            self.logger.info(f"JSON saved: {json_filepath}")
        
        if output_format in ['csv', 'both']:
            csv_filename = f'exercises_processed_{timestamp}.csv'
            csv_filepath = PROCESSED_DATA_DIR / csv_filename
            
            df_csv = df.copy()
            
            list_columns = ['primaryMuscles', 'secondaryMuscles', 'all_muscles', 'instructions', 'images']
            for col in list_columns:
                if col in df_csv.columns:
                    df_csv[col] = df_csv[col].apply(
                        lambda x: '|'.join(x) if isinstance(x, list) else ''
                    )
            
            save_to_csv(df_csv, csv_filepath)
            exported_files['csv'] = csv_filepath
            self.logger.info(f"CSV saved: {csv_filepath}")
        
        return exported_files
    
    def run(self, input_file: Path, output_format: str = 'both') -> Dict[str, Path]:
        """
        Execute complete processing pipeline
        
        Pipeline:
        1. Load raw data
        2. Validation
        3. Cleaning
        4. Normalization
        5. Enrichment
        6. Deduplication
        7. Export
        
        Args:
            input_file: Path to raw JSON file
            output_format: Export format ('json', 'csv', 'both')
            
        Returns:
            Dictionary of exported files
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting ExerciseDB processing pipeline")
        self.logger.info("=" * 60)
        
        try:
            metadata, df = self.load_raw_data(input_file)
            df = self.validate_data(df)
            df = self.clean_text_fields(df)
            df = self.normalize_muscle_groups(df)
            df = self.enrich_data(df)
            df = self.remove_duplicates(df)
            df = self.add_metadata_columns(df, metadata)
            exported_files = self.export_processed_data(df, metadata, output_format)
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Processing Statistics")
            self.logger.info("=" * 60)
            for key, value in self.stats.items():
                self.logger.info(f"{key}: {value}")
            
            self.logger.info("\n✅ Processing pipeline completed successfully")
            
            return exported_files
            
        except Exception as e:
            self.logger.error(f"❌ Error during processing: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    processor = ExerciseProcessor()
    
    raw_files = list(RAW_DATA_DIR.glob('exercisedb_raw_*.json'))
    
    if raw_files:
        latest_file = sorted(raw_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        
        print(f"\n📁 Source file: {latest_file.name}")
        
        exported = processor.run(latest_file, output_format='both')
        
        print("\n📤 Exported files:")
        for format_type, filepath in exported.items():
            print(f"  {format_type.upper()}: {filepath}")
    else:
        print("❌ No raw file found in data/raw/")
        print("💡 Run first: python -m src.scrapers.exercisedb_scraper")

"""
Processor to clean and transform ExerciseDB exercise data

Simplified using modular components:
- BaseProcessor: Common functionality
- ExerciseValidator: Validation logic
- ExerciseCleaner: Cleaning logic
- ExerciseEnricher: Enrichment logic
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

from src.processors.base_processor import BaseProcessor
from src.processors.validators import ExerciseValidator
from src.processors.cleaners import ExerciseCleaner
from src.processors.enrichers import ExerciseEnricher
from src.utils.file_handler import load_from_json
from config.settings import RAW_DATA_DIR


class ExerciseProcessor(BaseProcessor):
    """
    Processor to clean and transform exercise data
    
    Uses modular components for maintainability
    """
    
    def __init__(self):
        """Initialize processor"""
        super().__init__("ExerciseProcessor")
        self.metadata = {}
    
    def load_raw_data(self, filepath: Path) -> pd.DataFrame:
        """
        Load raw data from JSON file
        
        Args:
            filepath: Path to raw JSON file
            
        Returns:
            DataFrame of exercises
        """
        self.logger.info(f"Loading data from {filepath}")
        
        raw_data = load_from_json(filepath)
        self.metadata = raw_data.get('metadata', {})
        exercises = raw_data.get('exercises', [])
        df = pd.DataFrame(exercises)
        
        self.stats['total_records'] = len(df)
        self.logger.info(f"{len(df)} exercises loaded")
        
        return df
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data using ExerciseValidator
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validated DataFrame
        """
        self.logger.info("Validating data...")
        
        initial_count = len(df)
        df = ExerciseValidator.validate(df)
        
        self.stats['valid_records'] = len(df)
        self.stats['invalid_records'] = initial_count - len(df)
        
        self.logger.info(
            f"Validation complete: {self.stats['valid_records']} valid, "
            f"{self.stats['invalid_records']} rejected"
        )
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data using ExerciseCleaner
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        self.logger.info("Cleaning text fields...")
        
        df, fields_cleaned = ExerciseCleaner.clean(df)
        self.stats['fields_cleaned'] = fields_cleaned
        
        return df
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich data using ExerciseEnricher
        
        Args:
            df: DataFrame to enrich
            
        Returns:
            Enriched DataFrame
        """
        self.logger.info("Enriching data...")
        
        df = ExerciseEnricher.enrich_all(df)
        
        return df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicates using ExerciseCleaner
        
        Args:
            df: DataFrame to deduplicate
            
        Returns:
            Deduplicated DataFrame
        """
        self.logger.info("Removing duplicates...")
        
        df, duplicates_removed = ExerciseCleaner.remove_duplicates(df)
        self.stats['duplicates_removed'] = duplicates_removed
        
        self.logger.info(f"{duplicates_removed} duplicates removed")
        
        return df
    
    def run(self, input_file: Path, output_format: str = 'both') -> Dict[str, Path]:
        """
        Execute complete processing pipeline
        
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
            # Load data
            df = self.load_raw_data(input_file)
            
            # Run standard pipeline
            df = self.run_pipeline(
                df,
                data_source=self.metadata.get('source', 'ExerciseDB'),
                scraped_at=self.metadata.get('scraped_at')
            )
            
            # Export
            list_columns = ['primaryMuscles', 'secondaryMuscles', 'all_muscles', 'instructions', 'images']
            exported_files = self.export_processed_data(
                df,
                base_filename='exercises_processed',
                metadata=self.metadata,
                output_format=output_format,
                list_columns=list_columns
            )
            
            # Log statistics
            self.log_statistics()
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

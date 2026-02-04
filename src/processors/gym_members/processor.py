"""
Processor to clean and transform Gym Members dataset from Kaggle

Simplified using modular components:
- BaseProcessor: Common functionality
- GymMemberValidator: Validation logic
- GymMemberCleaner: Cleaning logic
- GymMemberEnricher: Enrichment logic
"""

import pandas as pd
from pathlib import Path
from typing import Dict

from src.processors.base_processor import BaseProcessor
from .validators import GymMemberValidator
from .cleaners import GymMemberCleaner
from .enrichers import GymMemberEnricher
from config.settings import RAW_DATA_DIR


class GymMembersProcessor(BaseProcessor):
    """
    Processor to clean and transform gym members data
    
    Uses modular components for maintainability
    """
    
    def __init__(self):
        """Initialize processor"""
        super().__init__("GymMembersProcessor")
    
    def load_raw_data(self, filepath: Path) -> pd.DataFrame:
        """
        Load raw data from CSV file
        
        Args:
            filepath: Path to raw CSV file
            
        Returns:
            DataFrame of gym members
        """
        self.logger.info(f"Loading data from {filepath}")
        
        df = pd.read_csv(filepath)
        
        self.stats['total_records'] = len(df)
        self.logger.info(f"{len(df)} members loaded")
        
        return df
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data using GymMemberValidator
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validated DataFrame
        """
        self.logger.info("Validating data...")
        
        initial_count = len(df)
        df = GymMemberValidator.validate(df)
        
        self.stats['valid_records'] = len(df)
        self.stats['invalid_records'] = initial_count - len(df)
        
        self.logger.info(
            f"Validation complete: {self.stats['valid_records']} valid, "
            f"{self.stats['invalid_records']} rejected"
        )
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data using GymMemberCleaner
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        self.logger.info("Cleaning text fields...")
        
        df, fields_cleaned = GymMemberCleaner.clean(df)
        self.stats['fields_cleaned'] = fields_cleaned
        
        return df
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich data using GymMemberEnricher
        
        Args:
            df: DataFrame to enrich
            
        Returns:
            Enriched DataFrame
        """
        self.logger.info("Enriching data...")
        
        df = GymMemberEnricher.enrich_all(df)
        
        return df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicates using GymMemberCleaner
        
        Args:
            df: DataFrame to deduplicate
            
        Returns:
            Deduplicated DataFrame
        """
        self.logger.info("Removing duplicates...")
        
        df, duplicates_removed = GymMemberCleaner.remove_duplicates(df)
        self.stats['duplicates_removed'] = duplicates_removed
        
        self.logger.info(f"{duplicates_removed} duplicates removed")
        
        return df
    
    def run(self, input_file: Path, output_format: str = 'both') -> Dict[str, Path]:
        """
        Execute complete processing pipeline
        
        Args:
            input_file: Path to raw CSV file
            output_format: Export format ('json', 'csv', 'both')
            
        Returns:
            Dictionary of exported files
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Gym Members processing pipeline")
        self.logger.info("=" * 60)
        
        try:
            # Load data
            df = self.load_raw_data(input_file)
            
            # Run standard pipeline
            df = self.run_pipeline(
                df,
                data_source='Kaggle - Gym Members Exercise Dataset'
            )
            
            # Export
            exported_files = self.export_processed_data(
                df,
                base_filename='gym_members_processed',
                output_format=output_format
            )
            
            # Log statistics
            self.log_statistics()
            self.logger.info("\n✅ Processing pipeline completed successfully")
            
            return exported_files
            
        except Exception as e:
            self.logger.error(f"❌ Error during processing: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    processor = GymMembersProcessor()
    
    # Find Kaggle gym members dataset
    kaggle_dir = RAW_DATA_DIR / 'kaggle' / 'gym-members-exercise-dataset'
    
    if kaggle_dir.exists():
        csv_files = list(kaggle_dir.glob('*.csv'))
        
        if csv_files:
            latest_file = csv_files[0]
            
            print(f"\n📁 Source file: {latest_file.name}")
            
            exported = processor.run(latest_file, output_format='both')
            
            print("\n📤 Exported files:")
            for format_type, filepath in exported.items():
                print(f"  {format_type.upper()}: {filepath}")
        else:
            print("❌ No CSV file found in Kaggle gym members directory")
    else:
        print("❌ Kaggle gym members dataset not found")
        print("💡 Run first: python -m src.scrapers.kaggle_scraper")

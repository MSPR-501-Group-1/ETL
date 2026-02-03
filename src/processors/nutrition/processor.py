"""
Processor to clean and transform Nutrition data

Simplified using modular components:
- BaseProcessor: Common functionality
- NutritionValidator: Validation logic
- NutritionCleaner: Cleaning logic
- NutritionEnricher: Enrichment logic
"""

import pandas as pd
from pathlib import Path
from typing import Dict

from src.processors.base_processor import BaseProcessor
from .validators import NutritionValidator
from .cleaners import NutritionCleaner
from .enrichers import NutritionEnricher
from config.settings import RAW_DATA_DIR


class NutritionProcessor(BaseProcessor):
    """
    Processor to clean and transform nutrition data
    
    Uses modular components for maintainability
    """
    
    def __init__(self):
        """Initialize processor"""
        super().__init__("NutritionProcessor")
    
    def load_raw_data(self, filepath: Path) -> pd.DataFrame:
        """
        Load raw data from file
        
        Args:
            filepath: Path to raw data file
            
        Returns:
            DataFrame of nutrition data
        """
        self.logger.info(f"Loading data from {filepath}")
        
        # TODO: Implement based on data source format (CSV, JSON, etc.)
        df = pd.read_csv(filepath)
        
        self.stats['total_records'] = len(df)
        self.logger.info(f"{len(df)} records loaded")
        
        return df
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data using NutritionValidator
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validated DataFrame
        """
        self.logger.info("Validating data...")
        
        initial_count = len(df)
        df = NutritionValidator.validate(df)
        
        self.stats['valid_records'] = len(df)
        self.stats['invalid_records'] = initial_count - len(df)
        
        self.logger.info(
            f"Validation complete: {self.stats['valid_records']} valid, "
            f"{self.stats['invalid_records']} rejected"
        )
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data using NutritionCleaner
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        self.logger.info("Cleaning data...")
        
        df, fields_cleaned = NutritionCleaner.clean(df)
        self.stats['fields_cleaned'] = fields_cleaned
        
        return df
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich data using NutritionEnricher
        
        Args:
            df: DataFrame to enrich
            
        Returns:
            Enriched DataFrame
        """
        self.logger.info("Enriching data...")
        
        df = NutritionEnricher.enrich_all(df)
        
        return df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicates using NutritionCleaner
        
        Args:
            df: DataFrame to deduplicate
            
        Returns:
            Deduplicated DataFrame
        """
        self.logger.info("Removing duplicates...")
        
        df, duplicates_removed = NutritionCleaner.remove_duplicates(df)
        self.stats['duplicates_removed'] = duplicates_removed
        
        self.logger.info(f"{duplicates_removed} duplicates removed")
        
        return df
    
    def run(self, input_file: Path, output_format: str = 'both') -> Dict[str, Path]:
        """
        Execute complete processing pipeline
        
        Args:
            input_file: Path to raw data file
            output_format: Export format ('json', 'csv', 'both')
            
        Returns:
            Dictionary of exported files
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Nutrition processing pipeline")
        self.logger.info("=" * 60)
        
        try:
            # Load data
            df = self.load_raw_data(input_file)
            
            # Run standard pipeline
            df = self.run_pipeline(
                df,
                data_source='Nutrition Dataset'
            )
            
            # Export
            exported_files = self.export_processed_data(
                df,
                base_filename='nutrition_processed',
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
    # TODO: Implement once nutrition data source is available
    print("Nutrition processor ready - waiting for data source")

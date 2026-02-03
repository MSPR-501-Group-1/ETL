"""
Base Processor - Abstract class for all data processors

Provides common functionality for all processors:
- Statistics tracking
- Metadata handling
- Export logic
- Pipeline orchestration
"""

import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from src.utils.logger import setup_logger
from src.utils.file_handler import save_to_json, save_to_csv
from config.settings import PROCESSED_DATA_DIR


class BaseProcessor(ABC):
    """
    Abstract base class for all data processors
    
    Child classes must implement:
    - validate_data()
    - clean_data()
    - enrich_data()
    - remove_duplicates()
    """
    
    def __init__(self, processor_name: str):
        """
        Initialize base processor
        
        Args:
            processor_name: Name of the processor (for logging)
        """
        self.logger = setup_logger(processor_name)
        self.stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'duplicates_removed': 0,
            'fields_cleaned': 0
        }
    
    @abstractmethod
    def load_raw_data(self, filepath: Path) -> pd.DataFrame:
        """
        Load raw data from file
        
        Args:
            filepath: Path to raw data file
            
        Returns:
            DataFrame with raw data
        """
        pass
    
    @abstractmethod
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data structure and values
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validated DataFrame
        """
        pass
    
    @abstractmethod
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize data
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        pass
    
    @abstractmethod
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich data with calculated fields
        
        Args:
            df: DataFrame to enrich
            
        Returns:
            Enriched DataFrame
        """
        pass
    
    @abstractmethod
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate records
        
        Args:
            df: DataFrame to deduplicate
            
        Returns:
            Deduplicated DataFrame
        """
        pass
    
    def add_metadata_columns(
        self,
        df: pd.DataFrame,
        data_source: str,
        scraped_at: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Add metadata columns for traceability
        
        Args:
            df: DataFrame to add metadata to
            data_source: Source of the data
            scraped_at: Original scraping timestamp (optional)
            
        Returns:
            DataFrame with metadata columns
        """
        df['data_source'] = data_source
        if scraped_at:
            df['scraped_at'] = scraped_at
        df['processed_at'] = datetime.now().isoformat()
        
        return df
    
    def export_processed_data(
        self,
        df: pd.DataFrame,
        base_filename: str,
        metadata: Optional[Dict] = None,
        output_format: str = 'both',
        list_columns: Optional[list] = None
    ) -> Dict[str, Path]:
        """
        Export processed data to JSON and/or CSV
        
        Args:
            df: Processed DataFrame
            base_filename: Base name for output files
            metadata: Metadata to include in JSON export
            output_format: 'json', 'csv' or 'both'
            list_columns: Columns containing lists (for CSV conversion)
            
        Returns:
            Dictionary of created file paths
        """
        self.logger.info(f"Exporting data in {output_format} format...")
        
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exported_files = {}
        
        if output_format in ['json', 'both']:
            json_filename = f'{base_filename}_{timestamp}.json'
            json_filepath = PROCESSED_DATA_DIR / json_filename
            
            output_data = {
                'metadata': {
                    **(metadata or {}),
                    'processing_stats': self.stats,
                    'processed_at': datetime.now().isoformat(),
                    'total_records': len(df)
                },
                'data': df.to_dict('records')
            }
            
            save_to_json(output_data, json_filepath)
            exported_files['json'] = json_filepath
            self.logger.info(f"JSON saved: {json_filepath}")
        
        if output_format in ['csv', 'both']:
            csv_filename = f'{base_filename}_{timestamp}.csv'
            csv_filepath = PROCESSED_DATA_DIR / csv_filename
            
            df_csv = df.copy()
            
            # Convert list columns to pipe-separated strings
            if list_columns:
                for col in list_columns:
                    if col in df_csv.columns:
                        df_csv[col] = df_csv[col].apply(
                            lambda x: '|'.join(x) if isinstance(x, list) else ''
                        )
            
            save_to_csv(df_csv, csv_filepath)
            exported_files['csv'] = csv_filepath
            self.logger.info(f"CSV saved: {csv_filepath}")
        
        return exported_files
    
    def log_statistics(self):
        """Log processing statistics"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Processing Statistics")
        self.logger.info("=" * 60)
        for key, value in self.stats.items():
            self.logger.info(f"{key}: {value}")
    
    def run_pipeline(
        self,
        df: pd.DataFrame,
        data_source: str,
        scraped_at: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Execute standard processing pipeline
        
        Pipeline steps:
        1. Validation
        2. Cleaning
        3. Enrichment
        4. Deduplication
        5. Add metadata
        
        Args:
            df: Raw DataFrame
            data_source: Source of the data
            scraped_at: Original scraping timestamp
            
        Returns:
            Processed DataFrame
        """
        df = self.validate_data(df)
        df = self.clean_data(df)
        df = self.enrich_data(df)
        df = self.remove_duplicates(df)
        df = self.add_metadata_columns(df, data_source, scraped_at)
        
        return df

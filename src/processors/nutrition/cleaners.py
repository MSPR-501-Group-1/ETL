"""
Nutrition data cleaners

Provides cleaning and normalization logic specific to nutrition data
"""

import pandas as pd
from typing import List, Tuple


class DataCleaner:
    """
    Generic data cleaner with reusable cleaning operations
    """
    
    @staticmethod
    def clean_text_fields(
        df: pd.DataFrame,
        columns: List[str],
        lowercase: bool = True,
        strip: bool = True
    ) -> pd.DataFrame:
        """
        Clean text fields (trim, lowercase)
        
        Args:
            df: DataFrame to clean
            columns: List of column names to clean
            lowercase: Convert to lowercase
            strip: Remove leading/trailing whitespace
            
        Returns:
            Cleaned DataFrame
        """
        for column in columns:
            if column in df.columns:
                if strip:
                    df[column] = df[column].apply(
                        lambda x: x.strip() if isinstance(x, str) else x
                    )
                if lowercase:
                    df[column] = df[column].apply(
                        lambda x: x.lower() if isinstance(x, str) else x
                    )
        
        return df
    
    @staticmethod
    def remove_duplicates(
        df: pd.DataFrame,
        subset: List[str] = None,
        keep: str = 'first'
    ) -> Tuple[pd.DataFrame, int]:
        """
        Remove duplicate records
        
        Args:
            df: DataFrame to deduplicate
            subset: Columns to consider for duplicates (None = all)
            keep: Which duplicate to keep ('first', 'last', False)
            
        Returns:
            Tuple of (deduplicated DataFrame, number of duplicates removed)
        """
        initial_count = len(df)
        df = df.drop_duplicates(subset=subset, keep=keep)
        duplicates_removed = initial_count - len(df)
        
        return df, duplicates_removed


class NutritionCleaner:
    """
    Specific cleaning logic for nutrition data
    """
    
    # TODO: Define text fields to clean based on data source
    TEXT_FIELDS = ['name']
    
    @staticmethod
    def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Clean nutrition data
        
        Args:
            df: Nutrition DataFrame
            
        Returns:
            Tuple of (cleaned DataFrame, number of fields cleaned)
        """
        fields_cleaned = 0
        
        # Clean text fields
        df = DataCleaner.clean_text_fields(
            df,
            NutritionCleaner.TEXT_FIELDS,
            lowercase=True,
            strip=True
        )
        fields_cleaned += len([f for f in NutritionCleaner.TEXT_FIELDS if f in df.columns])
        
        # TODO: Add specific cleaning logic for nutrition data
        
        return df, fields_cleaned
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Remove duplicate nutrition records
        
        Args:
            df: Nutrition DataFrame
            
        Returns:
            Tuple of (deduplicated DataFrame, number of duplicates removed)
        """
        # TODO: Define appropriate deduplication strategy
        df, count = DataCleaner.remove_duplicates(df, subset=['name'], keep='first')
        
        return df, count

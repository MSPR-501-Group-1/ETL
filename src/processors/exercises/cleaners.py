"""
Exercise data cleaners

Provides cleaning and normalization logic specific to exercise data
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


class ExerciseCleaner:
    """
    Specific cleaning logic for exercise data
    """
    
    TEXT_FIELDS = ['name', 'equipment', 'force', 'mechanic', 'category']
    
    @staticmethod
    def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Clean exercise data
        
        Args:
            df: Exercise DataFrame
            
        Returns:
            Tuple of (cleaned DataFrame, number of fields cleaned)
        """
        fields_cleaned = 0
        
        # Clean text fields
        df = DataCleaner.clean_text_fields(
            df,
            ExerciseCleaner.TEXT_FIELDS,
            lowercase=True,
            strip=True
        )
        fields_cleaned += len([f for f in ExerciseCleaner.TEXT_FIELDS if f in df.columns])
        
        return df, fields_cleaned
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Remove duplicate exercises
        
        Args:
            df: Exercise DataFrame
            
        Returns:
            Tuple of (deduplicated DataFrame, number of duplicates removed)
        """
        # First by ID
        df, count1 = DataCleaner.remove_duplicates(df, subset=['id'], keep='first')
        
        # Then by name
        df, count2 = DataCleaner.remove_duplicates(df, subset=['name'], keep='first')
        
        total_duplicates = count1 + count2
        
        return df, total_duplicates

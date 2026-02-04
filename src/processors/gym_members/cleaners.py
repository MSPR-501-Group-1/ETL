"""
Gym Members data cleaners

Provides cleaning and normalization logic specific to gym members data
"""

import pandas as pd
from typing import List, Dict, Tuple


class DataCleaner:
    """
    Generic data cleaner with reusable cleaning operations
    """
    
    @staticmethod
    def standardize_categorical(
        df: pd.DataFrame,
        column: str,
        mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Standardize categorical values using a mapping
        
        Args:
            df: DataFrame to clean
            column: Column name to standardize
            mapping: Dictionary mapping old values to new values
            
        Returns:
            Cleaned DataFrame
        """
        if column in df.columns:
            df[column] = df[column].replace(mapping)
        
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


class GymMemberCleaner:
    """
    Specific cleaning logic for gym member data
    """
    
    GENDER_MAPPING = {
        'male': 'M',
        'm': 'M',
        'female': 'F',
        'f': 'F'
    }
    
    EXPERIENCE_MAPPING = {
        '1': 'beginner',
        '2': 'intermediate',
        '3': 'expert'
    }
    
    @staticmethod
    def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Clean gym member data
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Tuple of (cleaned DataFrame, number of fields cleaned)
        """
        fields_cleaned = 0
        
        # Normalize gender
        if 'gender' in df.columns:
            df['gender'] = df['gender'].str.lower().str.strip()
            df = DataCleaner.standardize_categorical(
                df,
                'gender',
                GymMemberCleaner.GENDER_MAPPING
            )
            fields_cleaned += 1
        
        # Normalize workout type
        if 'workout_type' in df.columns:
            df['workout_type'] = df['workout_type'].str.lower().str.strip()
            fields_cleaned += 1
        
        # Normalize experience level
        if 'experience_level' in df.columns:
            df['experience_level'] = df['experience_level'].str.lower().str.strip()
            df = DataCleaner.standardize_categorical(
                df,
                'experience_level',
                GymMemberCleaner.EXPERIENCE_MAPPING
            )
            fields_cleaned += 1
        
        return df, fields_cleaned
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Remove duplicate gym members
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Tuple of (deduplicated DataFrame, number of duplicates removed)
        """
        duplicate_cols = []
        for col in ['age', 'gender', 'weight_(kg)', 'height_(m)']:
            if col in df.columns:
                duplicate_cols.append(col)
        
        if duplicate_cols:
            df, count = DataCleaner.remove_duplicates(df, subset=duplicate_cols, keep='first')
        else:
            count = 0
        
        return df, count

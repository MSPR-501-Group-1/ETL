"""
Data Cleaners - Cleaning and normalization logic

Provides reusable cleaning functions for common data operations
"""

import pandas as pd
from typing import List, Dict, Tuple


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
    def fill_missing_values(
        df: pd.DataFrame,
        column: str,
        strategy: str = 'mean',
        fill_value: any = None
    ) -> pd.DataFrame:
        """
        Fill missing values in a column
        
        Args:
            df: DataFrame to clean
            column: Column name
            strategy: 'mean', 'median', 'mode', 'constant'
            fill_value: Value to use if strategy is 'constant'
            
        Returns:
            Cleaned DataFrame
        """
        if column not in df.columns:
            return df
        
        if strategy == 'mean':
            df[column].fillna(df[column].mean(), inplace=True)
        elif strategy == 'median':
            df[column].fillna(df[column].median(), inplace=True)
        elif strategy == 'mode':
            df[column].fillna(df[column].mode()[0], inplace=True)
        elif strategy == 'constant':
            df[column].fillna(fill_value, inplace=True)
        
        return df


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

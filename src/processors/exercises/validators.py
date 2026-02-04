"""
Exercise data validators

Provides validation logic specific to exercise data
"""

import pandas as pd
from typing import List


class DataValidator:
    """
    Generic data validator with reusable validation rules
    """
    
    @staticmethod
    def validate_required_fields(df: pd.DataFrame, required_fields: List[str]) -> pd.DataFrame:
        """
        Ensure required fields exist and are not null
        
        Args:
            df: DataFrame to validate
            required_fields: List of required column names
            
        Returns:
            DataFrame with only records containing all required fields
        """
        # Add missing columns with None values
        for field in required_fields:
            if field not in df.columns:
                df[field] = None
        
        # Filter out records with any required field null
        mask = pd.Series([True] * len(df))
        for field in required_fields:
            mask &= df[field].notna()
        
        return df[mask].copy()
    
    @staticmethod
    def validate_categorical(
        df: pd.DataFrame,
        column: str,
        valid_values: List[str],
        default_value: str = None
    ) -> pd.DataFrame:
        """
        Validate categorical column contains only allowed values
        
        Args:
            df: DataFrame to validate
            column: Column name to validate
            valid_values: List of allowed values
            default_value: Default value for invalid entries (if None, filter out)
            
        Returns:
            Validated DataFrame
        """
        if column not in df.columns:
            return df
        
        if default_value:
            # Replace invalid values with default
            df[column] = df[column].apply(
                lambda x: x if x in valid_values else default_value
            )
        else:
            # Filter out invalid values
            df = df[df[column].isin(valid_values)]
        
        return df
    
    @staticmethod
    def validate_list_field(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Ensure list field is actually a list
        
        Args:
            df: DataFrame to validate
            column: Column name to validate
            
        Returns:
            DataFrame with validated list field
        """
        if column in df.columns:
            df[column] = df[column].apply(
                lambda x: x if isinstance(x, list) else []
            )
        
        return df


class ExerciseValidator:
    """
    Specific validators for exercise data
    """
    
    VALID_LEVELS = ['beginner', 'intermediate', 'expert']
    VALID_CATEGORIES = [
        'cardio', 'olympic weightlifting', 'plyometrics',
        'powerlifting', 'strength', 'stretching', 'strongman'
    ]
    REQUIRED_FIELDS = ['name', 'id', 'category', 'equipment', 'primaryMuscles']
    
    @staticmethod
    def validate(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate exercise data
        
        Args:
            df: Exercise DataFrame
            
        Returns:
            Validated DataFrame
        """
        validator = DataValidator()
        
        # Required fields
        df = validator.validate_required_fields(df, ExerciseValidator.REQUIRED_FIELDS)
        
        # Validate list fields
        for field in ['primaryMuscles', 'secondaryMuscles', 'instructions']:
            df = validator.validate_list_field(df, field)
        
        # Validate categorical fields
        df = validator.validate_categorical(
            df, 'level',
            ExerciseValidator.VALID_LEVELS,
            default_value='intermediate'
        )
        
        df = validator.validate_categorical(
            df, 'category',
            ExerciseValidator.VALID_CATEGORIES,
            default_value='strength'
        )
        
        return df

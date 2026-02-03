"""
Gym Members data validators

Provides validation logic specific to gym members data
"""

import pandas as pd
from typing import List


class DataValidator:
    """
    Generic data validator with reusable validation rules
    """
    
    @staticmethod
    def validate_numeric_range(
        df: pd.DataFrame,
        column: str,
        min_value: float,
        max_value: float
    ) -> pd.DataFrame:
        """
        Validate numeric column is within range
        
        Args:
            df: DataFrame to validate
            column: Column name to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Filtered DataFrame
        """
        if column in df.columns:
            df = df[(df[column] >= min_value) & (df[column] <= max_value)]
        
        return df
    
    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names (lowercase, replace spaces with underscores)
        
        Args:
            df: DataFrame to normalize
            
        Returns:
            DataFrame with normalized column names
        """
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        return df


class GymMemberValidator:
    """
    Specific validators for gym member data
    """
    
    NUMERIC_RANGES = {
        'age': (15, 100),
        'weight_(kg)': (30, 200),
        'height_(m)': (1.2, 2.2),
        'bmi': (10, 50),
        'max_bpm': (40, 220),
        'avg_bpm': (40, 220)
    }
    
    @staticmethod
    def validate(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate gym member data
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Validated DataFrame
        """
        validator = DataValidator()
        
        # Normalize column names
        df = validator.normalize_column_names(df)
        
        # Validate numeric ranges
        for column, (min_val, max_val) in GymMemberValidator.NUMERIC_RANGES.items():
            df = validator.validate_numeric_range(df, column, min_val, max_val)
        
        return df

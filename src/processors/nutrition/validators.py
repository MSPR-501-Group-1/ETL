"""
Nutrition data validators

Provides validation logic specific to nutrition data
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


class NutritionValidator:
    """
    Specific validators for nutrition data
    """
    
    # TODO: Define required fields and validation rules based on data source
    REQUIRED_FIELDS = ['name']
    
    @staticmethod
    def validate(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate nutrition data
        
        Args:
            df: Nutrition DataFrame
            
        Returns:
            Validated DataFrame
        """
        validator = DataValidator()
        
        # Required fields
        df = validator.validate_required_fields(df, NutritionValidator.REQUIRED_FIELDS)
        
        # TODO: Add specific validation rules for nutrition data
        # Example: validate_numeric_range for calories, proteins, etc.
        
        return df

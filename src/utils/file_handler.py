"""
File handling utilities for saving data
"""

import json
import pandas as pd
from pathlib import Path
from typing import Union, List, Dict
from datetime import datetime


def save_to_json(data: Union[List, Dict], filepath: Path, indent: int = 2) -> None:
    """
    Save data to JSON file
    
    Args:
        data: Data to save (list or dict)
        filepath: Path to save the file
        indent: JSON indentation level
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def save_to_csv(df: pd.DataFrame, filepath: Path) -> None:
    """
    Save DataFrame to CSV file
    
    Args:
        df: Pandas DataFrame to save
        filepath: Path to save the file
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False, encoding='utf-8')


def load_from_json(filepath: Path) -> Union[List, Dict]:
    """
    Load data from JSON file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_filename(base_name: str, extension: str = 'json') -> str:
    """
    Generate filename with timestamp
    
    Args:
        base_name: Base name for the file
        extension: File extension (without dot)
        
    Returns:
        Filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.{extension}"

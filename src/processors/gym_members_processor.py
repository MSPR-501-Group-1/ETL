"""
Processor to clean and transform Gym Members dataset from Kaggle

Applies following transformations:
1. Data structure validation
2. Field cleaning (normalization, null handling)
3. Data enrichment (BMI categories, fitness levels)
4. Deduplication and consistency
5. Export to usable format
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import setup_logger
from src.utils.file_handler import save_to_json, save_to_csv, load_from_json
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR


class GymMembersProcessor:
    """
    Processor to clean and transform gym members data
    
    Transformation pipeline:
    1. Load raw data
    2. Structure validation
    3. Cleaning and normalization
    4. Enrichment
    5. Export clean data
    """
    
    def __init__(self):
        """Initialize processor and logging system"""
        self.logger = setup_logger(self.__class__.__name__)
        self.stats = {
            'total_members': 0,
            'valid_members': 0,
            'invalid_members': 0,
            'duplicates_removed': 0,
            'fields_cleaned': 0
        }
    
    def load_raw_data(self, filepath: Path) -> pd.DataFrame:
        """
        Load raw data from CSV file
        
        Args:
            filepath: Path to raw CSV file
            
        Returns:
            DataFrame of gym members
        """
        self.logger.info(f"Loading data from {filepath}")
        
        df = pd.read_csv(filepath)
        
        self.stats['total_members'] = len(df)
        self.logger.info(f"{len(df)} members loaded")
        
        return df
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data structure and consistency
        
        Validation rules:
        - Age: 15-100 years
        - Weight: 30-200 kg
        - Height: 120-220 cm
        - BMI: 10-50
        - Heart rate: 40-220 bpm
        
        Args:
            df: Members DataFrame
            
        Returns:
            DataFrame with only valid members
        """
        self.logger.info("Validating data...")
        
        initial_count = len(df)
        
        # Normalize column names (lowercase, remove spaces)
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Validate age
        if 'age' in df.columns:
            df = df[(df['age'] >= 15) & (df['age'] <= 100)]
        
        # Validate weight
        if 'weight_(kg)' in df.columns:
            df = df[(df['weight_(kg)'] >= 30) & (df['weight_(kg)'] <= 200)]
        
        # Validate height
        if 'height_(m)' in df.columns:
            df = df[(df['height_(m)'] >= 1.2) & (df['height_(m)'] <= 2.2)]
        
        # Validate BMI
        if 'bmi' in df.columns:
            df = df[(df['bmi'] >= 10) & (df['bmi'] <= 50)]
        
        # Validate heart rate
        if 'max_bpm' in df.columns:
            df = df[(df['max_bpm'] >= 40) & (df['max_bpm'] <= 220)]
        if 'avg_bpm' in df.columns:
            df = df[(df['avg_bpm'] >= 40) & (df['avg_bpm'] <= 220)]
        
        self.stats['valid_members'] = len(df)
        self.stats['invalid_members'] = initial_count - len(df)
        
        self.logger.info(
            f"Validation complete: {self.stats['valid_members']} valid, "
            f"{self.stats['invalid_members']} rejected"
        )
        
        return df
    
    def clean_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize text fields
        
        Operations:
        - Normalize gender values
        - Standardize workout types
        - Clean experience levels
        
        Args:
            df: Members DataFrame
            
        Returns:
            DataFrame with cleaned text fields
        """
        self.logger.info("Cleaning text fields...")
        
        # Normalize gender
        if 'gender' in df.columns:
            df['gender'] = df['gender'].str.lower().str.strip()
            df['gender'] = df['gender'].replace({
                'male': 'M',
                'm': 'M',
                'female': 'F',
                'f': 'F'
            })
            self.stats['fields_cleaned'] += 1
        
        # Normalize workout type
        if 'workout_type' in df.columns:
            df['workout_type'] = df['workout_type'].str.lower().str.strip()
            self.stats['fields_cleaned'] += 1
        
        # Normalize experience level
        if 'experience_level' in df.columns:
            df['experience_level'] = df['experience_level'].str.lower().str.strip()
            df['experience_level'] = df['experience_level'].replace({
                '1': 'beginner',
                '2': 'intermediate',
                '3': 'expert'
            })
            self.stats['fields_cleaned'] += 1
        
        return df
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich data with calculated fields
        
        Additions:
        - BMI category
        - Age group
        - Fitness level score
        - Heart rate zones
        - Calorie burn rate
        
        Args:
            df: Members DataFrame
            
        Returns:
            Enriched DataFrame
        """
        self.logger.info("Enriching data...")
        
        # BMI Category
        if 'bmi' in df.columns:
            def categorize_bmi(bmi):
                if bmi < 18.5:
                    return 'underweight'
                elif bmi < 25:
                    return 'normal'
                elif bmi < 30:
                    return 'overweight'
                else:
                    return 'obese'
            
            df['bmi_category'] = df['bmi'].apply(categorize_bmi)
        
        # Age Group
        if 'age' in df.columns:
            def categorize_age(age):
                if age < 25:
                    return '18-24'
                elif age < 35:
                    return '25-34'
                elif age < 45:
                    return '35-44'
                elif age < 55:
                    return '45-54'
                else:
                    return '55+'
            
            df['age_group'] = df['age'].apply(categorize_age)
        
        # Fitness Score (based on multiple factors)
        if all(col in df.columns for col in ['max_bpm', 'calories_burned', 'workout_frequency_(days/week)']):
            df['fitness_score'] = (
                (df['max_bpm'] / 220 * 20) +
                (df['calories_burned'] / 100 * 30) +
                (df['workout_frequency_(days/week)'] * 10)
            ).round(2)
        
        # Heart Rate Reserve (HRR)
        if 'max_bpm' in df.columns and 'avg_bpm' in df.columns:
            df['heart_rate_reserve'] = df['max_bpm'] - df['avg_bpm']
        
        # Calorie Burn Rate (calories per session)
        if 'calories_burned' in df.columns and 'session_duration_(hours)' in df.columns:
            df['calorie_burn_rate'] = (
                df['calories_burned'] / df['session_duration_(hours)']
            ).round(2)
        
        # Body Fat Category
        if 'body_fat_%' in df.columns and 'gender' in df.columns:
            def categorize_body_fat(row):
                bf = row['body_fat_%']
                gender = row['gender']
                
                if gender == 'M':
                    if bf < 6:
                        return 'essential'
                    elif bf < 14:
                        return 'athletic'
                    elif bf < 18:
                        return 'fit'
                    elif bf < 25:
                        return 'average'
                    else:
                        return 'obese'
                else:  # Female
                    if bf < 14:
                        return 'essential'
                    elif bf < 21:
                        return 'athletic'
                    elif bf < 25:
                        return 'fit'
                    elif bf < 32:
                        return 'average'
                    else:
                        return 'obese'
            
            df['body_fat_category'] = df.apply(categorize_body_fat, axis=1)
        
        # Experience Level Score
        if 'experience_level' in df.columns:
            experience_scores = {
                'beginner': 1,
                'intermediate': 2,
                'expert': 3
            }
            df['experience_score'] = df['experience_level'].map(experience_scores)
        
        return df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate members
        
        Strategy:
        - Identify duplicates by combination of age, gender, weight, height
        - Keep most recent entry
        
        Args:
            df: Members DataFrame
            
        Returns:
            Deduplicated DataFrame
        """
        self.logger.info("Removing duplicates...")
        
        initial_count = len(df)
        
        duplicate_cols = []
        for col in ['age', 'gender', 'weight_(kg)', 'height_(m)']:
            if col in df.columns:
                duplicate_cols.append(col)
        
        if duplicate_cols:
            df = df.drop_duplicates(subset=duplicate_cols, keep='first')
        
        self.stats['duplicates_removed'] = initial_count - len(df)
        self.logger.info(f"{self.stats['duplicates_removed']} duplicates removed")
        
        return df
    
    def add_metadata_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add metadata columns for traceability
        
        Args:
            df: Members DataFrame
            
        Returns:
            DataFrame with metadata
        """
        df['data_source'] = 'Kaggle - Gym Members Exercise Dataset'
        df['processed_at'] = datetime.now().isoformat()
        
        return df
    
    def export_processed_data(
        self,
        df: pd.DataFrame,
        output_format: str = 'both'
    ) -> Dict[str, Path]:
        """
        Export processed data to JSON and/or CSV
        
        Args:
            df: Processed members DataFrame
            output_format: 'json', 'csv' or 'both'
            
        Returns:
            Dictionary of created file paths
        """
        self.logger.info(f"Exporting data in {output_format} format...")
        
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exported_files = {}
        
        if output_format in ['json', 'both']:
            json_filename = f'gym_members_processed_{timestamp}.json'
            json_filepath = PROCESSED_DATA_DIR / json_filename
            
            output_data = {
                'metadata': {
                    'source': 'Kaggle - Gym Members Exercise Dataset',
                    'processing_stats': self.stats,
                    'processed_at': datetime.now().isoformat(),
                    'total_processed_members': len(df)
                },
                'members': df.to_dict('records')
            }
            
            save_to_json(output_data, json_filepath)
            exported_files['json'] = json_filepath
            self.logger.info(f"JSON saved: {json_filepath}")
        
        if output_format in ['csv', 'both']:
            csv_filename = f'gym_members_processed_{timestamp}.csv'
            csv_filepath = PROCESSED_DATA_DIR / csv_filename
            
            save_to_csv(df, csv_filepath)
            exported_files['csv'] = csv_filepath
            self.logger.info(f"CSV saved: {csv_filepath}")
        
        return exported_files
    
    def run(self, input_file: Path, output_format: str = 'both') -> Dict[str, Path]:
        """
        Execute complete processing pipeline
        
        Pipeline:
        1. Load raw data
        2. Validation
        3. Cleaning
        4. Enrichment
        5. Deduplication
        6. Export
        
        Args:
            input_file: Path to raw CSV file
            output_format: Export format ('json', 'csv', 'both')
            
        Returns:
            Dictionary of exported files
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Gym Members processing pipeline")
        self.logger.info("=" * 60)
        
        try:
            df = self.load_raw_data(input_file)
            df = self.validate_data(df)
            df = self.clean_text_fields(df)
            df = self.enrich_data(df)
            df = self.remove_duplicates(df)
            df = self.add_metadata_columns(df)
            exported_files = self.export_processed_data(df, output_format)
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Processing Statistics")
            self.logger.info("=" * 60)
            for key, value in self.stats.items():
                self.logger.info(f"{key}: {value}")
            
            self.logger.info("\n✅ Processing pipeline completed successfully")
            
            return exported_files
            
        except Exception as e:
            self.logger.error(f"❌ Error during processing: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    processor = GymMembersProcessor()
    
    # Find Kaggle gym members dataset
    kaggle_dir = RAW_DATA_DIR / 'kaggle' / 'gym-members-exercise-dataset'
    
    if kaggle_dir.exists():
        csv_files = list(kaggle_dir.glob('*.csv'))
        
        if csv_files:
            latest_file = csv_files[0]
            
            print(f"\n📁 Source file: {latest_file.name}")
            
            exported = processor.run(latest_file, output_format='both')
            
            print("\n📤 Exported files:")
            for format_type, filepath in exported.items():
                print(f"  {format_type.upper()}: {filepath}")
        else:
            print("❌ No CSV file found in Kaggle gym members directory")
    else:
        print("❌ Kaggle gym members dataset not found")
        print("💡 Run first: python -m src.scrapers.kaggle_scraper")

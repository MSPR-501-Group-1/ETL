"""
Data Enrichers - Enrichment logic for different data types

Provides reusable enrichment functions to add calculated fields
"""

import pandas as pd
from typing import List, Dict


class ExerciseEnricher:
    """
    Enrichment logic specific to exercise data
    """
    
    # Muscle name mapping for normalization
    MUSCLE_MAPPING = {
        'abs': 'abdominals',
        'quads': 'quadriceps',
        'lats': 'lats',
        'traps': 'trapezius',
    }
    
    # Movement categorization keywords
    PUSH_INDICATORS = ['push', 'press', 'chest', 'triceps', 'shoulders']
    PULL_INDICATORS = ['pull', 'row', 'back', 'biceps', 'lats']
    
    @staticmethod
    def normalize_muscle_groups(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize and enrich muscle groups
        
        Adds:
        - all_muscles: Combined primary + secondary
        - muscle_count: Total muscles targeted
        - exercise_type: compound or isolation
        
        Args:
            df: Exercise DataFrame
            
        Returns:
            Enriched DataFrame
        """
        def normalize_muscle_list(muscles):
            """Normalize muscle list"""
            if not isinstance(muscles, list):
                return []
            return [ExerciseEnricher.MUSCLE_MAPPING.get(m.lower(), m.lower()) for m in muscles]
        
        df['primaryMuscles'] = df['primaryMuscles'].apply(normalize_muscle_list)
        df['secondaryMuscles'] = df['secondaryMuscles'].apply(normalize_muscle_list)
        
        df['all_muscles'] = df.apply(
            lambda row: list(set(row['primaryMuscles'] + row['secondaryMuscles'])),
            axis=1
        )
        
        df['muscle_count'] = df['all_muscles'].apply(len)
        
        df['exercise_type'] = df['muscle_count'].apply(
            lambda x: 'compound' if x > 2 else 'isolation'
        )
        
        return df
    
    @staticmethod
    def add_difficulty_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add difficulty-related metrics
        
        Adds:
        - difficulty_score: Numerical score (1-3)
        - instruction_count: Number of instruction steps
        - complexity_score: Combined difficulty + instruction complexity
        
        Args:
            df: Exercise DataFrame
            
        Returns:
            Enriched DataFrame
        """
        level_scores = {'beginner': 1, 'intermediate': 2, 'expert': 3}
        df['difficulty_score'] = df['level'].map(level_scores)
        
        df['instruction_count'] = df['instructions'].apply(len)
        df['complexity_score'] = df.apply(
            lambda row: row['difficulty_score'] + (row['instruction_count'] / 10),
            axis=1
        )
        
        return df
    
    @staticmethod
    def add_equipment_classification(df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify exercises by equipment requirement
        
        Adds:
        - requires_equipment: Boolean
        
        Args:
            df: Exercise DataFrame
            
        Returns:
            Enriched DataFrame
        """
        df['requires_equipment'] = df['equipment'].apply(
            lambda x: x not in ['body only', 'none', None]
        )
        
        return df
    
    @staticmethod
    def add_movement_categorization(df: pd.DataFrame) -> pd.DataFrame:
        """
        Categorize exercises by movement type
        
        Adds:
        - movement_type: push, pull, cardio, stretching, other
        
        Args:
            df: Exercise DataFrame
            
        Returns:
            Enriched DataFrame
        """
        def categorize_movement(row):
            """Categorize movement type"""
            name_lower = row['name'].lower() if isinstance(row['name'], str) else ''
            
            if any(word in name_lower for word in ExerciseEnricher.PUSH_INDICATORS):
                return 'push'
            elif any(word in name_lower for word in ExerciseEnricher.PULL_INDICATORS):
                return 'pull'
            elif row['category'] in ['cardio', 'stretching']:
                return row['category']
            else:
                return 'other'
        
        df['movement_type'] = df.apply(categorize_movement, axis=1)
        
        return df
    
    @staticmethod
    def enrich_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all exercise enrichments
        
        Args:
            df: Exercise DataFrame
            
        Returns:
            Fully enriched DataFrame
        """
        df = ExerciseEnricher.normalize_muscle_groups(df)
        df = ExerciseEnricher.add_difficulty_metrics(df)
        df = ExerciseEnricher.add_equipment_classification(df)
        df = ExerciseEnricher.add_movement_categorization(df)
        
        return df


class GymMemberEnricher:
    """
    Enrichment logic specific to gym member data
    """
    
    @staticmethod
    def add_bmi_category(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add BMI category classification
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Enriched DataFrame
        """
        if 'bmi' not in df.columns:
            return df
        
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
        
        return df
    
    @staticmethod
    def add_age_group(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add age group classification
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Enriched DataFrame
        """
        if 'age' not in df.columns:
            return df
        
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
        
        return df
    
    @staticmethod
    def add_fitness_score(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate fitness score based on multiple factors
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Enriched DataFrame
        """
        required_cols = ['max_bpm', 'calories_burned', 'workout_frequency_(days/week)']
        
        if all(col in df.columns for col in required_cols):
            df['fitness_score'] = (
                (df['max_bpm'] / 220 * 20) +
                (df['calories_burned'] / 100 * 30) +
                (df['workout_frequency_(days/week)'] * 10)
            ).round(2)
        
        return df
    
    @staticmethod
    def add_heart_rate_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add heart rate-related metrics
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Enriched DataFrame
        """
        if 'max_bpm' in df.columns and 'avg_bpm' in df.columns:
            df['heart_rate_reserve'] = df['max_bpm'] - df['avg_bpm']
        
        return df
    
    @staticmethod
    def add_calorie_burn_rate(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate calorie burn rate per hour
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Enriched DataFrame
        """
        if 'calories_burned' in df.columns and 'session_duration_(hours)' in df.columns:
            df['calorie_burn_rate'] = (
                df['calories_burned'] / df['session_duration_(hours)']
            ).round(2)
        
        return df
    
    @staticmethod
    def add_body_fat_category(df: pd.DataFrame) -> pd.DataFrame:
        """
        Categorize body fat percentage by gender
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Enriched DataFrame
        """
        if 'body_fat_%' not in df.columns or 'gender' not in df.columns:
            return df
        
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
        
        return df
    
    @staticmethod
    def add_experience_score(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add numerical experience score
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Enriched DataFrame
        """
        if 'experience_level' not in df.columns:
            return df
        
        experience_scores = {
            'beginner': 1,
            'intermediate': 2,
            'expert': 3
        }
        df['experience_score'] = df['experience_level'].map(experience_scores)
        
        return df
    
    @staticmethod
    def enrich_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all gym member enrichments
        
        Args:
            df: Gym member DataFrame
            
        Returns:
            Fully enriched DataFrame
        """
        df = GymMemberEnricher.add_bmi_category(df)
        df = GymMemberEnricher.add_age_group(df)
        df = GymMemberEnricher.add_fitness_score(df)
        df = GymMemberEnricher.add_heart_rate_metrics(df)
        df = GymMemberEnricher.add_calorie_burn_rate(df)
        df = GymMemberEnricher.add_body_fat_category(df)
        df = GymMemberEnricher.add_experience_score(df)
        
        return df

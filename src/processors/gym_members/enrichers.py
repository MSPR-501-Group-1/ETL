"""
Gym Members data enrichers

Provides enrichment logic specific to gym members data
"""

import pandas as pd


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

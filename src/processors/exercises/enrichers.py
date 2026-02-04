"""
Exercise data enrichers

Provides enrichment logic specific to exercise data
"""

import pandas as pd


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

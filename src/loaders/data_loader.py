"""
Loader pour charger les données processed dans une base existante
Base créée via les scripts SQL dans data/sql/
"""

import sqlite3
import json
import glob
import uuid
from pathlib import Path
from src.utils.logger import setup_logger


class DataLoader:
    """Loader pour charger les données ETL processed"""
    
    def __init__(self, db_path="data/healthai_coach.db"):
        self.db_path = Path(db_path)
        self.logger = setup_logger(self.__class__.__name__)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de données non trouvée: {db_path}")
    
    def load_exercises(self, json_file_path: str):
        """Charger les exercices depuis le fichier JSON processed"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        exercises = data.get('data', [])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for exercise in exercises:
            cursor.execute("""
                INSERT OR REPLACE INTO exercises (
                    exercise_id, name, body_part_target, equipment_required, category,
                    level, difficulty_score, complexity_score, muscle_count,
                    exercise_type, movement_type, requires_equipment,
                    all_muscles, primary_muscles, secondary_muscles, instructions,
                    data_source, scraped_at, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exercise.get('id'),
                exercise.get('name'),
                '|'.join(exercise.get('primaryMuscles', [])),
                exercise.get('equipment'),
                exercise.get('category'),
                exercise.get('level'),
                exercise.get('difficulty_score'),
                exercise.get('complexity_score'),
                exercise.get('muscle_count'),
                exercise.get('exercise_type'),
                exercise.get('movement_type'),
                exercise.get('requires_equipment', False),
                json.dumps(exercise.get('all_muscles', [])),
                json.dumps(exercise.get('primaryMuscles', [])),
                json.dumps(exercise.get('secondaryMuscles', [])),
                json.dumps(exercise.get('instructions', [])),
                exercise.get('data_source'),
                exercise.get('scraped_at'),
                exercise.get('processed_at')
            ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"✅ {len(exercises)} exercices chargés")
        return len(exercises)
    
    def load_gym_members(self, json_file_path: str):
        """Charger les profils gym depuis le fichier JSON processed"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        members = data.get('data', [])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for member in members:
            metric_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_metrics (
                    metric_id, user_id, recorded_date, weight_kg, body_fat_percentage,
                    age, gender, height_m, bmi, bmi_category, experience_level,
                    fitness_score, age_group, max_bpm, avg_bpm,
                    workout_frequency_days_week, session_duration_hours,
                    calorie_burn_rate, heart_rate_reserve, body_fat_category,
                    experience_score, data_source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric_id, user_id, '2026-02-03',
                member.get('weight_(kg)'), member.get('body_fat_%'),
                member.get('age'), member.get('gender'), member.get('height_(m)'),
                member.get('bmi'), member.get('bmi_category'),
                member.get('experience_level'), member.get('fitness_score'),
                member.get('age_group'), member.get('max_bpm'), member.get('avg_bpm'),
                member.get('workout_frequency_(days/week)'),
                member.get('session_duration_(hours)'),
                member.get('calorie_burn_rate'), member.get('heart_rate_reserve'),
                member.get('body_fat_category'), member.get('experience_score'),
                member.get('data_source'), member.get('processed_at', '2026-02-03T10:00:00')
            ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"✅ {len(members)} profils membres chargés")
        return len(members)
    
    def load_all_processed(self):
        """Charger tous les fichiers processed automatiquement"""
        self.logger.info("🔍 Recherche des fichiers processed...")
        
        total_loaded = 0
        
        # Exercices
        exercise_files = glob.glob('data/processed/exercises_processed_*.json')
        if exercise_files:
            latest = max(exercise_files, key=lambda x: Path(x).stat().st_mtime)
            count = self.load_exercises(latest)
            total_loaded += count
        else:
            self.logger.warning("Aucun fichier exercises_processed_*.json trouvé")
        
        # Gym members
        member_files = glob.glob('data/processed/gym_members_processed_*.json')
        if member_files:
            latest = max(member_files, key=lambda x: Path(x).stat().st_mtime)
            count = self.load_gym_members(latest)
            total_loaded += count
        else:
            self.logger.warning("Aucun fichier gym_members_processed_*.json trouvé")
        
        self.logger.info(f"🎯 Chargement terminé: {total_loaded} enregistrements")
        return total_loaded
    
    def get_stats(self):
        """Afficher les statistiques de la base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        tables = ['exercises', 'user_metrics', 'health_goals', 'subscription_plans']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except sqlite3.Error:
                stats[table] = 0
        
        conn.close()
        return stats


if __name__ == "__main__":
    import sys
    
    try:
        loader = DataLoader()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "load":
                loader.load_all_processed()
            elif command == "stats":
                stats = loader.get_stats()
                print("\n📊 Statistiques de la base:")
                for table, count in stats.items():
                    print(f"  {table}: {count} enregistrements")
            else:
                print("Commandes: load, stats")
        else:
            # Chargement par défaut
            loader.load_all_processed()
            stats = loader.get_stats()
            print(f"\n📈 Données chargées: {sum(stats.values())} enregistrements total")
            
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 Créez d'abord la base avec: sqlite3 data/database.db < data/sql/01_create_tables.sql")
"""
HealthAI Coach - ETL Main Entry Point
"""
import sys
import argparse
from processors.exercises.pipeline import run_pipeline as run_exercises_pipeline
from processors.nutrition.pipeline import run_pipeline as run_nutrition_pipeline
from processors.nutrition_values.pipeline import run_pipeline as run_nutrition_values_pipeline
from processors.gym_members.pipeline import run_pipeline as run_gym_members_pipeline
from processors.body_performance.pipeline import run_pipeline as run_body_performance_pipeline
from processors.fitness_tracker.pipeline import run_pipeline as run_fitness_tracker_pipeline

def main():
    """Main ETL orchestrator"""
    parser = argparse.ArgumentParser(description='HealthAI Coach ETL Pipeline')
    parser.add_argument(
        '--pipeline',
        choices=['exercises', 'nutrition', 'nutrition-values', 'nutrition-all', 
                 'gym-members', 'body-performance', 'fitness-tracker', 'all'],
        default='all',
        help='Pipeline to run (nutrition-all runs both nutrition sources, all runs everything)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🏥 HEALTHAI COACH - ETL PIPELINE")
    print("=" * 70)
    
    success = True
    failed_pipelines = []
    
    if args.pipeline == 'exercises' or args.pipeline == 'all':
        print("\n🏋️  Running EXERCISES pipeline...")
        try:
            if not run_exercises_pipeline():
                success = False
                failed_pipelines.append("Exercises")
        except Exception as e:
            print(f"❌ EXERCISES pipeline failed: {e}")
            success = False
            failed_pipelines.append("Exercises")
    
    if args.pipeline == 'nutrition' or args.pipeline == 'nutrition-all' or args.pipeline == 'all':
        print("\n🍎 Running NUTRITION pipeline (Daily Food)...")
        try:
            if not run_nutrition_pipeline():
                success = False
                failed_pipelines.append("Nutrition")
        except Exception as e:
            print(f"❌ NUTRITION pipeline failed: {e}")
            success = False
            failed_pipelines.append("Nutrition")
    
    if args.pipeline == 'nutrition-values' or args.pipeline == 'nutrition-all' or args.pipeline == 'all':
        print("\n🥗 Running NUTRITION VALUES pipeline (Common Foods)...")
        try:
            if not run_nutrition_values_pipeline():
                success = False
                failed_pipelines.append("Nutrition Values")
        except Exception as e:
            print(f"❌ NUTRITION VALUES pipeline failed: {e}")
            success = False
            failed_pipelines.append("Nutrition Values")
    
    if args.pipeline == 'gym-members' or args.pipeline == 'all':
        print("\n👥 Running GYM MEMBERS pipeline...")
        try:
            if not run_gym_members_pipeline():
                success = False
                failed_pipelines.append("Gym Members")
        except Exception as e:
            print(f"❌ GYM MEMBERS pipeline failed: {e}")
            success = False
            failed_pipelines.append("Gym Members")
    
    if args.pipeline == 'body-performance' or args.pipeline == 'all':
        print("\n💪 Running BODY PERFORMANCE pipeline...")
        try:
            if not run_body_performance_pipeline():
                success = False
                failed_pipelines.append("Body Performance")
        except Exception as e:
            print(f"❌ BODY PERFORMANCE pipeline failed: {e}")
            success = False
            failed_pipelines.append("Body Performance")
    
    if args.pipeline == 'fitness-tracker' or args.pipeline == 'all':
        print("\n📱 Running FITNESS TRACKER pipeline...")
        try:
            if not run_fitness_tracker_pipeline():
                success = False
                failed_pipelines.append("Fitness Tracker")
        except Exception as e:
            print(f"❌ FITNESS TRACKER pipeline failed: {e}")
            success = False
            failed_pipelines.append("Fitness Tracker")
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ETL COMPLETED SUCCESSFULLY")
    else:
        print("❌ ETL COMPLETED WITH FAILURES")
        print(f"   Failed pipelines: {', '.join(failed_pipelines)}")
        if any(p in failed_pipelines for p in ["Nutrition", "Nutrition Values", "Gym Members", "Body Performance", "Fitness Tracker"]):
            print("\n💡 Note: Kaggle pipelines require credentials.")
            print("   Set KAGGLE_USERNAME and KAGGLE_KEY environment variables,")
            print("   or mount ~/.kaggle/kaggle.json in docker-compose.yml")
    print("=" * 70)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

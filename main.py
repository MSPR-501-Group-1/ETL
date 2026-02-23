"""
HealthAI Coach - ETL Main Entry Point
"""
import sys
import argparse
from processors.exercises.pipeline import run_pipeline as run_exercises_pipeline
from processors.nutrition.pipeline import run_pipeline as run_nutrition_pipeline
from processors.nutrition_values.pipeline import run_pipeline as run_nutrition_values_pipeline

def main():
    """Main ETL orchestrator"""
    parser = argparse.ArgumentParser(description='HealthAI Coach ETL Pipeline')
    parser.add_argument(
        '--pipeline',
        choices=['exercises', 'nutrition', 'nutrition-values', 'nutrition-all', 'users', 'all'],
        default='exercises',
        help='Pipeline to run (nutrition-all runs both nutrition sources)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🏥 HEALTHAI COACH - ETL PIPELINE")
    print("=" * 70)
    
    success = True
    
    if args.pipeline == 'exercises' or args.pipeline == 'all':
        print("\n🏋️  Running EXERCISES pipeline...")
        success = run_exercises_pipeline() and success
    
    if args.pipeline == 'nutrition' or args.pipeline == 'nutrition-all' or args.pipeline == 'all':
        print("\n🍎 Running NUTRITION pipeline (Daily Food)...")
        success = run_nutrition_pipeline() and success
    
    if args.pipeline == 'nutrition-values' or args.pipeline == 'nutrition-all' or args.pipeline == 'all':
        print("\n🥗 Running NUTRITION VALUES pipeline (Common Foods)...")
        success = run_nutrition_values_pipeline() and success
    
    if args.pipeline == 'users' or args.pipeline == 'all':
        print("\n👤 USERS pipeline: TODO")
        # success = run_users_pipeline() and success
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ETL COMPLETED SUCCESSFULLY")
    else:
        print("❌ ETL FAILED")
    print("=" * 70)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

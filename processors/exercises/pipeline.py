"""
Complete ETL pipeline orchestrator for exercises
"""
from spark.session import get_spark, stop_spark
from processors.exercises.extract import download_exercises
from processors.exercises.transform import transform_exercises
from processors.exercises.load import load_exercises
from processors.exercises.config import LOCAL_FILE

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    print("=" * 60)
    print("🚀 EXERCISES ETL PIPELINE START")
    print("=" * 60)
    
    # Step 1: Extract
    print("\n📥 STEP 1/3: EXTRACT")
    print("-" * 60)
    data = download_exercises()
    
    if not data:
        print("❌ Extraction failed. Aborting pipeline.")
        return False
    
    print(f"✅ Extracted {len(data)} exercises")
    
    # Step 2: Transform
    print("\n🔄 STEP 2/3: TRANSFORM")
    print("-" * 60)
    spark = get_spark("Exercises_Pipeline")
    
    try:
        df_transformed = transform_exercises(spark, str(LOCAL_FILE))
        
        if df_transformed is None or df_transformed.count() == 0:
            print("❌ Transformation failed. Aborting pipeline.")
            return False
        
        print(f"✅ Transformed {df_transformed.count()} exercises")
        
        # Step 3: Load
        print("\n📦 STEP 3/3: LOAD")
        print("-" * 60)
        success = load_exercises(spark, df_transformed)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"📊 Summary:")
            print(f"   - Extracted: {len(data)} exercises")
            print(f"   - Transformed: {df_transformed.count()} exercises")
            print(f"   - Loaded: PostgreSQL + Parquet + CSV")
            return True
        else:
            print("\n❌ Load failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        return False
        
    finally:
        stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)

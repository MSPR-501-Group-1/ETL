"""
Complete ETL pipeline orchestrator for fitness tracker
Loads ACTIVITY_TYPE and WORKOUT_SESSION tables
"""
from spark.session import get_spark, stop_spark
from processors.fitness_tracker.extract import download_fitness_tracker
from processors.fitness_tracker.transform import transform_fitness_tracker
from processors.fitness_tracker.load import load_fitness_tracker
from processors.fitness_tracker.config import LOCAL_FILE

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    print("=" * 60)
    print("🚀 FITNESS TRACKER ETL PIPELINE START")
    print("=" * 60)
    
    # Step 1: Extract
    print("\n📥 STEP 1/3: EXTRACT")
    print("-" * 60)
    success = download_fitness_tracker()
    
    if not success:
        print("❌ Extraction failed. Aborting pipeline.")
        return False
    
    # Quick count of extracted data
    spark = get_spark("Fitness_Tracker_Pipeline")
    try:
        import pandas as pd
        df_raw = pd.read_csv(str(LOCAL_FILE))
        print(f"✅ Extracted {len(df_raw)} fitness tracker records from Kaggle")
    except:
        print(f"✅ Dataset downloaded: {LOCAL_FILE}")
    
    # Step 2: Transform
    print("\n🔄 STEP 2/3: TRANSFORM")
    print("-" * 60)
    
    try:
        df_activities, df_sessions = transform_fitness_tracker(spark, str(LOCAL_FILE))
        
        if df_activities is None or df_activities.count() == 0:
            print("❌ Transformation failed. Aborting pipeline.")
            return False
        
        print(f"✅ Transformed {df_activities.count()} activity types and {df_sessions.count()} sessions")
        
        # Step 3: Load
        print("\n📦 STEP 3/3: LOAD")
        print("-" * 60)
        success = load_fitness_tracker(spark, df_activities, df_sessions)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"📊 Summary:")
            print(f"   - Extracted: {LOCAL_FILE}")
            print(f"   - Transformed: {df_activities.count()} activity types, {df_sessions.count()} sessions")
            print(f"   - Loaded to: PostgreSQL (activity_type, workout_session)")
            print(f"   - Saved: Parquet + CSV formats")
            return True
        else:
            print("\n❌ Load failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)

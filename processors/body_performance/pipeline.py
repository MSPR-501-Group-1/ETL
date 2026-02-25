"""
Complete ETL pipeline orchestrator for body performance
Loads WORKOUT_SESSION and SESSION_DETAIL tables
"""
from spark.session import get_spark, stop_spark
from processors.body_performance.extract import download_body_performance
from processors.body_performance.transform import transform_body_performance
from processors.body_performance.load import load_body_performance
from processors.body_performance.config import LOCAL_FILE

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    print("=" * 60)
    print("🚀 BODY PERFORMANCE ETL PIPELINE START")
    print("=" * 60)
    
    # Step 1: Extract
    print("\n📥 STEP 1/3: EXTRACT")
    print("-" * 60)
    success = download_body_performance()
    
    if not success:
        print("❌ Extraction failed. Aborting pipeline.")
        return False
    
    # Quick count of extracted data
    spark = get_spark("Body_Performance_Pipeline")
    try:
        import pandas as pd
        df_raw = pd.read_csv(str(LOCAL_FILE))
        print(f"✅ Extracted {len(df_raw)} body performance records from Kaggle")
    except:
        print(f"✅ Dataset downloaded: {LOCAL_FILE}")
    
    # Step 2: Transform
    print("\n🔄 STEP 2/3: TRANSFORM")
    print("-" * 60)
    
    try:
        df_sessions, df_details = transform_body_performance(spark, str(LOCAL_FILE))
        
        if df_sessions is None or df_sessions.count() == 0:
            print("❌ Transformation failed. Aborting pipeline.")
            return False
        
        detail_msg = f" and {df_details.count()} details" if df_details else ""
        print(f"✅ Transformed {df_sessions.count()} sessions{detail_msg}")
        
        # Step 3: Load
        print("\n📦 STEP 3/3: LOAD")
        print("-" * 60)
        success = load_body_performance(spark, df_sessions, df_details)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"📊 Summary:")
            print(f"   - Extracted: {LOCAL_FILE}")
            print(f"   - Transformed: {df_sessions.count()} sessions{detail_msg}")
            print(f"   - Loaded to: PostgreSQL (workout_session, session_detail)")
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

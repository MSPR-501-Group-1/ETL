"""
Complete ETL pipeline orchestrator for gym members
Loads USER, USER_PROFILE, and USER_METRICS tables
"""
from spark.session import get_spark, stop_spark
from processors.gym_members.extract import download_gym_members
from processors.gym_members.transform import transform_gym_members
from processors.gym_members.load import load_gym_members
from processors.gym_members.config import LOCAL_FILE

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    print("=" * 60)
    print("🚀 GYM MEMBERS ETL PIPELINE START")
    print("=" * 60)
    
    # Step 1: Extract
    print("\n📥 STEP 1/3: EXTRACT")
    print("-" * 60)
    success = download_gym_members()
    
    if not success:
        print("❌ Extraction failed. Aborting pipeline.")
        return False
    
    # Quick count of extracted data
    spark = get_spark("Gym_Members_Pipeline")
    try:
        import pandas as pd
        df_raw = pd.read_csv(str(LOCAL_FILE))
        print(f"✅ Extracted {len(df_raw)} gym members from Kaggle")
    except:
        print(f"✅ Dataset downloaded: {LOCAL_FILE}")
    
    # Step 2: Transform
    print("\n🔄 STEP 2/3: TRANSFORM")
    print("-" * 60)
    
    try:
        df_user, df_profile, df_metrics = transform_gym_members(spark, str(LOCAL_FILE))
        
        if df_user is None or df_user.count() == 0:
            print("❌ Transformation failed. Aborting pipeline.")
            return False
        
        print(f"✅ Transformed {df_user.count()} gym members into 3 tables")
        
        # Step 3: Load
        print("\n📦 STEP 3/3: LOAD")
        print("-" * 60)
        success = load_gym_members(spark, df_user, df_profile, df_metrics)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"📊 Summary:")
            print(f"   - Extracted: {LOCAL_FILE}")
            print(f"   - Transformed: {df_user.count()} users")
            print(f"   - Loaded to: PostgreSQL (user, user_profile, user_metrics)")
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

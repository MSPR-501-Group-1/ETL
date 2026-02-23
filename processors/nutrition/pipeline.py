"""
Complete ETL pipeline orchestrator for nutrition
"""
from spark.session import get_spark, stop_spark
from processors.nutrition.extract import download_nutrition
from processors.nutrition.transform import transform_nutrition
from processors.nutrition.load import load_nutrition
from processors.nutrition.config import LOCAL_FILE

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    print("=" * 60)
    print("🚀 NUTRITION ETL PIPELINE START")
    print("=" * 60)
    
    # Step 1: Extract
    print("\n📥 STEP 1/3: EXTRACT")
    print("-" * 60)
    file_path = download_nutrition()
    
    if not file_path:
        print("❌ Extraction failed. Aborting pipeline.")
        return False
    
    print(f"✅ Extracted data to {file_path}")
    
    # Step 2: Transform
    print("\n🔄 STEP 2/3: TRANSFORM")
    print("-" * 60)
    spark = get_spark("Nutrition_Pipeline")
    
    try:
        df_transformed = transform_nutrition(spark, str(LOCAL_FILE))
        
        if df_transformed is None or df_transformed.count() == 0:
            print("❌ Transformation failed. Aborting pipeline.")
            return False
        
        print(f"✅ Transformed {df_transformed.count()} foods")
        
        # Step 3: Load
        print("\n📦 STEP 3/3: LOAD")
        print("-" * 60)
        success = load_nutrition(spark, df_transformed)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"📊 Summary:")
            print(f"   - Extracted: CSV from Kaggle")
            print(f"   - Transformed: {df_transformed.count()} foods")
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

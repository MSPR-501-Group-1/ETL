"""
Complete ETL pipeline orchestrator for nutrition values
Source: Kaggle - nutritional-values-for-common-foods-and-products
"""
from spark.session import get_spark, stop_spark
from processors.nutrition_values.extract import download_nutrition_values
from processors.nutrition_values.transform import transform_nutrition_values
from processors.nutrition_values.load import load_nutrition_values
from processors.nutrition_values.config import LOCAL_FILE

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    print("=" * 60)
    print("🚀 NUTRITION VALUES ETL PIPELINE START")
    print("=" * 60)
    print("📊 Source: Nutritional Values for Common Foods")
    print()
    
    # Step 1: Extract
    print("\n📥 STEP 1/3: EXTRACT")
    print("-" * 60)
    file_path = download_nutrition_values()
    
    if not file_path:
        print("❌ Extraction failed. Aborting pipeline.")
        return False
    
    print(f"✅ Extracted data to {file_path}")
    
    # Step 2: Transform
    print("\n🔄 STEP 2/3: TRANSFORM")
    print("-" * 60)
    spark = get_spark("Nutrition_Values_Pipeline")
    
    try:
        df_transformed = transform_nutrition_values(spark, str(LOCAL_FILE))
        
        if df_transformed is None or df_transformed.count() == 0:
            print("❌ Transformation failed. Aborting pipeline.")
            return False
        
        print(f"✅ Transformed {df_transformed.count()} foods")
        
        # Step 3: Load
        print("\n📦 STEP 3/3: LOAD")
        print("-" * 60)
        success = load_nutrition_values(spark, df_transformed)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"📊 Summary:")
            print(f"   - Source: Kaggle nutritional-values dataset")
            print(f"   - Extracted: CSV with nutritional data")
            print(f"   - Transformed: {df_transformed.count()} foods")
            print(f"   - Loaded: PostgreSQL (food table) + Parquet + CSV")
            print(f"\n💡 Note: Data appended to existing 'food' table")
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

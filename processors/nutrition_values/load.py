"""
Load transformed nutrition values data to PostgreSQL
"""
from pyspark.sql import DataFrame

from utils.load import log_etl_execution, save_to_csv, save_to_parquet, save_to_postgres


def load_nutrition_values(spark, df: DataFrame) -> bool:
    """Complete load pipeline: Parquet + CSV + PostgreSQL"""
    print("⏳ Loading nutrition values data...")
    
    from processors.nutrition_values.config import PROCESSED_DIR, OUTPUT_PARQUET, OUTPUT_CSV
    
    try:
        # 1. Save to Parquet
        save_to_parquet(df, str(OUTPUT_PARQUET))
        
        # 2. Save to CSV
        save_to_csv(df, str(OUTPUT_CSV))
        
        # 3. Load to PostgreSQL
        success = save_to_postgres(df, "food")
        
        if success:
            log_etl_execution(spark, "SUCCESS", df.count(), SOURCE_NAME="nutrition_values")
            print("✅ Load completed")
            return True
        else:
            log_etl_execution(spark, "FAILED", 0, "PostgreSQL load failed", SOURCE_NAME="nutrition_values")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Load error - {e}")
        log_etl_execution(spark, "FAILED", 0, str(e), SOURCE_NAME="nutrition_values")
        return False

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.nutrition_values.transform import transform_nutrition_values
    from processors.nutrition_values.config import LOCAL_FILE
    
    spark = get_spark("Load_Nutrition_Values")
    
    try:
        print("🔄 Running transformation...")
        df_transformed = transform_nutrition_values(spark, str(LOCAL_FILE))
        
        if df_transformed:
            success = load_nutrition_values(spark, df_transformed)
            
            if success:
                print("\n" + "=" * 60)
                print("🎉 ETL PIPELINE COMPLETED")
                print("=" * 60)
                print(f"✅ Data available in:")
                print(f"   - PostgreSQL: food table (appended)")
                print(f"   - Parquet: data/processed/nutrition_values.parquet")
                print(f"   - CSV: data/processed/nutrition_values_csv/")
        else:
            print("❌ Transformation failed")
        
    finally:
        stop_spark()

"""
Load transformed nutrition data to PostgreSQL
"""
from pyspark.sql import DataFrame

from utils.load import log_etl_execution, save_to_csv, save_to_parquet, save_to_postgres


def load_nutrition(spark, df: DataFrame) -> bool:
    """Complete load pipeline: Parquet + CSV + PostgreSQL"""
    print("⏳ Loading nutrition data...")
    
    from processors.nutrition.config import PROCESSED_DIR
    
    try:
        # 1. Save to Parquet
        parquet_path = str(PROCESSED_DIR / "nutrition.parquet")
        save_to_parquet(df, parquet_path)
        
        # 2. Save to CSV
        csv_path = str(PROCESSED_DIR / "nutrition_csv")
        save_to_csv(df, csv_path)
        
        # 3. Load to PostgreSQL
        success = save_to_postgres(df, "food")
        
        if success:
            log_etl_execution(spark, "SUCCESS", df.count(), SOURCE_NAME="nutrition")
            print("✅ Load completed")
            return True
        else:
            log_etl_execution(spark, "FAILED", 0, "PostgreSQL load failed", SOURCE_NAME="nutrition")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Load error - {e}")
        log_etl_execution(spark, "FAILED", 0, str(e), SOURCE_NAME="nutrition")
        return False

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.nutrition.transform import transform_nutrition
    from processors.nutrition.config import LOCAL_FILE
    
    spark = get_spark("Load_Nutrition")
    
    try:
        print("🔄 Running transformation...")
        df_transformed = transform_nutrition(spark, str(LOCAL_FILE))
        
        success = load_nutrition(spark, df_transformed)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 ETL PIPELINE COMPLETED")
            print("=" * 60)
            print(f"✅ Data available in:")
            print(f"   - PostgreSQL: food table")
            print(f"   - Parquet: data/processed/nutrition.parquet")
            print(f"   - CSV: data/processed/nutrition_csv/")
        
    finally:
        stop_spark()

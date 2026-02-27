"""
Load transformed exercises data to PostgreSQL
"""
import os
from pyspark.sql import DataFrame
from datetime import datetime

from utils.load import log_etl_execution, save_to_csv, save_to_parquet, save_to_postgres

def load_exercises(spark, df: DataFrame) -> bool:
    """
    Complete load pipeline: Parquet + CSV + PostgreSQL
    
    Args:
        spark: Spark session
        df: Transformed DataFrame
        
    Returns:
        bool: Success status
    """
    print("⏳ Loading exercises data...")
    
    from processors.exercises.config import PROCESSED_DIR
    
    try:
        # 1. Save to Parquet (optimized format)
        parquet_path = str(PROCESSED_DIR / "exercises.parquet")
        save_to_parquet(df, parquet_path)
        
        # 2. Save to CSV (for exports)
        csv_path = str(PROCESSED_DIR / "exercises_csv")
        save_to_csv(df, csv_path)
        
        # 3. Load to PostgreSQL
        success = save_to_postgres(df, "exercise")
        
        if success:
            # Log successful execution
            log_etl_execution(spark, "SUCCESS", df.count(), SOURCE_NAME="exercises")
            print("✅ Load completed")
            return True
        else:
            log_etl_execution(spark, "FAILED", 0, "PostgreSQL load failed", SOURCE_NAME="exercises")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Load error - {e}")
        log_etl_execution(spark, "FAILED", 0, str(e), SOURCE_NAME="exercises")
        return False

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.exercises.transform import transform_exercises
    from processors.exercises.config import LOCAL_FILE
    
    spark = get_spark("Load_Exercises")
    
    try:
        # Transform data first
        print("🔄 Running transformation...")
        df_transformed = transform_exercises(spark, str(LOCAL_FILE))
        
        # Load to destinations
        success = load_exercises(spark, df_transformed)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 ETL PIPELINE COMPLETED")
            print("=" * 60)
            print(f"✅ Data available in:")
            print(f"   - PostgreSQL: exercise table")
            print(f"   - Parquet: data/processed/exercises.parquet")
            print(f"   - CSV: data/processed/exercises_csv/")
        
    finally:
        stop_spark()

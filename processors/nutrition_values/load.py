"""
Load transformed nutrition values data to PostgreSQL
"""
import os
from pyspark.sql import DataFrame
from processors.exercises.load import (
    get_db_config, get_jdbc_url, 
    save_to_parquet, save_to_csv, log_etl_execution
)

def save_to_postgres(df: DataFrame, table_name: str = "food"):
    """
    Save DataFrame to PostgreSQL using JDBC
    
    Note: Uses APPEND mode to add to existing food table
    Mode can be changed to OVERWRITE if needed
    """
    print(f"🗄️  Loading to PostgreSQL table: {table_name}")
    
    config = get_db_config()
    jdbc_url = get_jdbc_url()
    
    connection_properties = {
        "user": config["user"],
        "password": config["password"],
        "driver": "org.postgresql.Driver"
    }
    
    try:
        # Using APPEND mode to add to existing food table
        # Change to "overwrite" if you want to replace all data
        df.write.jdbc(
            url=jdbc_url,
            table=table_name,
            mode="append",  # Append to existing data
            properties=connection_properties
        )
        
        count = df.count()
        print(f"✅ Loaded {count} rows to PostgreSQL (mode: append)")
        return True
        
    except Exception as e:
        print(f"❌ Error loading to PostgreSQL: {e}")
        return False

def load_nutrition_values(spark, df: DataFrame) -> bool:
    """Complete load pipeline: Parquet + CSV + PostgreSQL"""
    print("=" * 60)
    print("📦 LOAD NUTRITION VALUES DATA")
    print("=" * 60)
    
    from processors.nutrition_values.config import PROCESSED_DIR, OUTPUT_PARQUET, OUTPUT_CSV
    
    try:
        # 1. Save to Parquet
        print(f"\n💾 Saving to Parquet: {OUTPUT_PARQUET}")
        save_to_parquet(df, str(OUTPUT_PARQUET))
        
        # 2. Save to CSV
        print(f"\n💾 Saving to CSV: {OUTPUT_CSV}")
        save_to_csv(df, str(OUTPUT_CSV))
        
        # 3. Load to PostgreSQL
        print(f"\n💾 Loading to PostgreSQL...")
        success = save_to_postgres(df, "food")
        
        if success:
            log_etl_execution(spark, "SUCCESS", df.count())
            print("\n✅ Load completed successfully!")
            return True
        else:
            log_etl_execution(spark, "FAILED", 0, "PostgreSQL load failed")
            print("\n❌ Load failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Load error: {e}")
        log_etl_execution(spark, "FAILED", 0, str(e))
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

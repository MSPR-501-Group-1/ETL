"""
Load transformed nutrition data to PostgreSQL
"""
import os
from pyspark.sql import DataFrame
from processors.exercises.load import (
    get_db_config, get_jdbc_url, 
    save_to_parquet, save_to_csv, log_etl_execution
)

def save_to_postgres(df: DataFrame, table_name: str = "food"):
    """Save DataFrame to PostgreSQL using JDBC"""
    print(f"🗄️  Loading to PostgreSQL table: {table_name}")
    
    config = get_db_config()
    jdbc_url = get_jdbc_url()
    
    connection_properties = {
        "user": config["user"],
        "password": config["password"],
        "driver": "org.postgresql.Driver"
    }
    
    try:
        df.write.jdbc(
            url=jdbc_url,
            table=table_name,
            mode="overwrite",
            properties=connection_properties
        )
        
        count = df.count()
        print(f"✅ Loaded {count} rows to PostgreSQL")
        return True
        
    except Exception as e:
        print(f"❌ Error loading to PostgreSQL: {e}")
        return False

def load_nutrition(spark, df: DataFrame) -> bool:
    """Complete load pipeline: Parquet + CSV + PostgreSQL"""
    print("=" * 60)
    print("📦 LOAD NUTRITION DATA")
    print("=" * 60)
    
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

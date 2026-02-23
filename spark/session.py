"""
Spark session manager - Singleton pattern
Compatible with Java 21+
"""
from pyspark.sql import SparkSession
from pyspark.conf import SparkConf

class SparkSessionManager:
    """Singleton to manage Spark session"""
    
    _instance = None
    _spark = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SparkSessionManager, cls).__new__(cls)
        return cls._instance
    
    def get_session(self, app_name: str = "HealthAI_ETL") -> SparkSession:
        """Get or create Spark session"""
        if self._spark is None:
            builder = SparkSession.builder \
                .appName(app_name) \
                .master("local[*]") \
                .config("spark.driver.memory", "2g") \
                .config("spark.sql.adaptive.enabled", "true")
            
            # Add PostgreSQL JDBC driver if available
            import os
            jdbc_jar = "/app/jars/postgresql-42.7.1.jar"
            if os.path.exists(jdbc_jar):
                builder = builder.config("spark.jars", jdbc_jar)
            
            self._spark = builder.getOrCreate()
            
            self._spark.sparkContext.setLogLevel("WARN")
        
        return self._spark
    
    def stop(self):
        """Stop Spark session"""
        if self._spark is not None:
            self._spark.stop()
            self._spark = None

# Global instance
spark_manager = SparkSessionManager()

def get_spark(app_name: str = "HealthAI_ETL") -> SparkSession:
    """Get Spark session"""
    return spark_manager.get_session(app_name)

def stop_spark():
    """Stop Spark session"""
    spark_manager.stop()

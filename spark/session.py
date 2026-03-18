"""
Spark session manager - Singleton pattern
Compatible with Java 21+
"""
from pyspark.sql import SparkSession

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
            # Suppress Python warnings
            import warnings
            warnings.filterwarnings('ignore')
            
            builder = SparkSession.builder \
                .appName(app_name) \
                .master("local[*]") \
                .config("spark.driver.memory", "2g") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.shuffle.partitions", "4") \
                .config("spark.ui.showConsoleProgress", "false") \
                .config("spark.ui.enabled", "false") \
                .config("spark.python.profile", "false") \
                .config("spark.python.worker.reuse", "true")
            
            # Add PostgreSQL JDBC driver if available
            import os
            jdbc_jar = "/app/jars/postgresql-42.7.1.jar"
            if os.path.exists(jdbc_jar):
                builder = builder.config("spark.jars", jdbc_jar)
            
            self._spark = builder.getOrCreate()
            
            # Set log levels to FATAL (only show critical errors)
            self._spark.sparkContext.setLogLevel("FATAL")
            
            # Suppress ALL verbose logging
            import logging
            logging.getLogger("py4j").setLevel(logging.CRITICAL)
            logging.getLogger("pyspark").setLevel(logging.CRITICAL)
            logging.getLogger("py4j.java_gateway").setLevel(logging.CRITICAL)
            
            # Suppress Java logging via log4j
            try:
                log4j = self._spark._jvm.org.apache.log4j
                log4j.LogManager.getRootLogger().setLevel(log4j.Level.FATAL)
                log4j.Logger.getLogger("org").setLevel(log4j.Level.FATAL)
                log4j.Logger.getLogger("akka").setLevel(log4j.Level.FATAL)
                log4j.Logger.getLogger("org.apache.spark").setLevel(log4j.Level.FATAL)
                log4j.Logger.getLogger("org.apache.hadoop").setLevel(log4j.Level.FATAL)
            except Exception:
                pass  # If log4j config fails, continue anyway
        
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

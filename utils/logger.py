"""
Centralized logging configuration for ETL pipelines
"""
import logging
from pyspark.logger import PySparkLogger
import sys
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def get_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (typically module name)
        log_file: Optional specific log file name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # Prevent duplicate logs
        
        # Console handler with minimal formatting for clean output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_format)
        
        # File handler with detailed formatting
        if log_file is None:
            log_file = f"{name.replace('.', '_')}.log"
        
        file_handler = logging.FileHandler(LOGS_DIR / log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        # Add run separator to log file
        logger.debug("=" * 80)
        logger.debug(f"NEW RUN STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.debug("=" * 80)
    
    return logger

def log_dataframe_info(logger: logging.Logger, df, name: str):
    """Helper to log DataFrame information"""
    try:
        count = df.count()
        logger.info(f"{name}: {count:,} records")
        return count
    except Exception as e:
        logger.warning(f"Could not get count for {name}: {e}")
        return 0

def log_pipeline_start(logger: logging.Logger, pipeline_name: str):
    """Log start of pipeline with clear separator"""
    logger.info(f"{'='*60}")
    logger.info(f"🚀 {pipeline_name} - STARTING")
    logger.info(f"{'='*60}")

def log_pipeline_success(logger: logging.Logger, pipeline_name: str, details: str = ""):
    """Log successful pipeline completion"""
    logger.info(f"{'='*60}")
    logger.info(f"✅ {pipeline_name} - SUCCESS")
    if details:
        logger.info(f"   {details}")
    logger.info(f"{'='*60}")

def log_pipeline_failure(logger: logging.Logger, pipeline_name: str, error: str = ""):
    """Log pipeline failure"""
    logger.error(f"{'='*60}")
    logger.error(f"❌ {pipeline_name} - FAILED")
    if error:
        logger.error(f"   Error: {error}")
    logger.error(f"{'='*60}")

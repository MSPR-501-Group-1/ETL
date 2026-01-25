"""
Global settings and configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = BASE_DIR / os.getenv('RAW_DATA_PATH', 'data/raw')
PROCESSED_DATA_DIR = BASE_DIR / os.getenv('PROCESSED_DATA_PATH', 'data/processed')
LOGS_DIR = BASE_DIR / 'data' / 'logs'

SCRAPING_CONFIG = {
    'user_agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
    'request_delay': int(os.getenv('REQUEST_DELAY', 1)),
    'max_retries': int(os.getenv('MAX_RETRIES', 3)),
    'timeout': int(os.getenv('TIMEOUT', 30))
}

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = BASE_DIR / os.getenv('LOG_FILE', 'data/logs/etl.log')

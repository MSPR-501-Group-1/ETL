import json
from pathlib import Path

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


def download_github(LOCAL_FILE: Path, URLS: list = None, force_download: bool = False) -> Path | None:
    """Download exercises data from GitHub and return the cached file path."""
    logger.info("⏳ Extracting exercises data...")

    if LOCAL_FILE.exists() and not force_download:
        logger.info("✅ Extract completed (from cache)")
        return LOCAL_FILE

    for i, url in enumerate(URLS, 1):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                continue
            with open(LOCAL_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("✅ Extract completed")
            return LOCAL_FILE
        except requests.exceptions.RequestException as e:
            logger.warning(f"Source {i} failed: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Source {i} JSON parse error: {e}")

    logger.error("❌ All sources failed")
    return None
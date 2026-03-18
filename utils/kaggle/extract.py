import os
import subprocess
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


def _check_kaggle_credentials() -> bool:
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        if not (os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")):
            logger.error("❌ Kaggle credentials not found")
            return False
    return True


def download_kaggle(LOCAL_ZIP: Path, LOCAL_FILE: Path, RAW_DIR: Path, KAGGLE_DATASET: str) -> str | None:
    """Download a Kaggle dataset and normalize the extracted CSV filename."""
    logger.info(f"⏳ Extracting Kaggle dataset: {KAGGLE_DATASET}...")

    if LOCAL_FILE.exists():
        logger.info("✅ Extract completed (from cache)")
        return str(LOCAL_FILE)

    if not _check_kaggle_credentials():
        return None

    try:
        subprocess.run(
            ["kaggle", "datasets", "download", "-d", KAGGLE_DATASET, "-p", str(RAW_DIR), "--unzip"],
            capture_output=True, text=True, check=True,
        )

        if not LOCAL_FILE.exists():
            csv_files = list(RAW_DIR.glob("*.csv"))
            if csv_files:
                csv_files[0].rename(LOCAL_FILE)
            else:
                logger.error("❌ No CSV file found after extraction")
                return None

        if LOCAL_FILE.exists():
            logger.info("✅ Extract completed")
            return str(LOCAL_FILE)

        logger.error("❌ File not found after extraction")
        return None

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Download error: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error("❌ Kaggle CLI not found")
        return None
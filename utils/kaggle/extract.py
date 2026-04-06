from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


def download_kaggle(local_file: Path, raw_dir: Path, dataset: str) -> str | None:
    """Download and extract a Kaggle dataset, returns the CSV path or None."""
    logger.info(f"⏳ Extracting Kaggle dataset: {dataset}...")

    if local_file.exists():
        logger.info("✅ Extract completed (from cache)")
        return str(local_file)

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
    except ImportError:
        logger.error("❌ kaggle package not installed (pip install kaggle)")
        return None
    except Exception as e:
        logger.error(f"❌ Kaggle auth failed: {e}")
        return None

    try:
        raw_dir.mkdir(parents=True, exist_ok=True)
        api.dataset_download_files(dataset, path=str(raw_dir), unzip=True, quiet=False)

        if not local_file.exists():
            csv_files = list(raw_dir.glob("*.csv"))
            if not csv_files:
                logger.error("❌ No CSV found after extraction")
                return None
            if len(csv_files) > 1:
                logger.warning(f"⚠️ Multiple CSVs found, using: {csv_files[0].name}")
            csv_files[0].rename(local_file)

        logger.info("✅ Extract completed")
        return str(local_file)

    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        return None
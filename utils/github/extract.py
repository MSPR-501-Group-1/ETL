from pathlib import Path

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


def download_github(
    local_file: Path,
    urls: list[str],
    *,
    force_download: bool = False,
) -> Path | None:
    """Download exercises JSON from GitHub fallback URLs, cache to *local_file*."""
    if local_file.exists() and not force_download:
        logger.info("✅ Extract completed (from cache)")
        return local_file

    logger.info("⏳ Extracting exercises data...")

    with requests.Session() as session:
        # Try each URL in order until one succeeds
        for i, url in enumerate(urls, 1):
            try:
                response = session.get(url, timeout=30)
                response.raise_for_status()

                if not isinstance(response.json(), list):
                    logger.warning(f"Source {i}: unexpected format (not a JSON array), skipping")
                    continue

                local_file.write_text(response.text, encoding="utf-8")
                logger.info("✅ Extract completed")
                return local_file

            except requests.exceptions.RequestException as e:
                logger.warning(f"Source {i} failed: {e}")
            except requests.exceptions.JSONDecodeError as e:
                logger.warning(f"Source {i} JSON parse error: {e}")

    logger.error("❌ All sources failed")
    return None
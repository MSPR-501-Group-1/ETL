
import os
from pathlib import Path

from pyspark.sql import DataFrame

from utils.logger import get_logger

logger = get_logger(__name__)

# Root of the project (two levels up from this file)
_REPORTS_DIR = Path(__file__).parent.parent / "reports"


def is_profiling_enabled() -> bool:
    return os.environ.get("ENABLE_PROFILING", "false").lower() == "true"


def profile_dataframe(
    df: DataFrame,
    pipeline_name: str,
    sample_size: int = 5000,
) -> None:

    if not is_profiling_enabled():
        return

    try:
        from ydata_profiling import ProfileReport
    except ImportError:
        logger.warning("ydata-profiling is not installed — skipping profiling")
        return

    try:
        logger.info(f"📊 Profiling '{pipeline_name}' (sample={sample_size})...")

        pdf = df.limit(sample_size).toPandas() if sample_size else df.toPandas()

        report = ProfileReport(
            pdf,
            title=f"{pipeline_name} — Data Profile",
            explorative=True,
            minimal=False,
        )

        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = _REPORTS_DIR / f"{pipeline_name}_profile.html"
        report.to_file(str(output_path))

        logger.info(f"✅ Profile report saved → {output_path}")

    except Exception as e:
        logger.warning(f"Profiling failed for '{pipeline_name}' (pipeline continues): {e}")

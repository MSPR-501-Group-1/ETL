"""
Main script to run all scrapers sequentially

This file orchestrates the complete data collection process:
1. Download exercises from ExerciseDB (GitHub)
2. Download 4 datasets from Kaggle
3. Display summary of successes/failures

Usage: python -m src.scrapers.run_scraping
"""

from pathlib import Path
from src.scrapers.exercisedb_scraper import ExerciseDBScraper
from src.scrapers.kaggle_scraper import KaggleDatasetScraper
from src.utils.logger import setup_logger


def main():
    """
    Main function: run all scrapers in order
    
    Process:
    1. Initialize logging system
    2. Execute ExerciseDB scraper
    3. Execute Kaggle downloads
    4. Display final summary
    """
    logger = setup_logger("ScrapingPipeline")
    
    logger.info("=" * 60)
    logger.info("Starting ETL Scraping Pipeline")
    logger.info("=" * 60)
    
    results = {}
    
    logger.info("\n[1/2] Downloading exercises from ExerciseDB (GitHub)...")
    try:
        exercisedb_scraper = ExerciseDBScraper()
        results['exercisedb'] = exercisedb_scraper.run()
    except Exception as e:
        logger.error(f"ExerciseDB scraping failed: {e}")
        results['exercisedb'] = None
    
    logger.info("\n[2/2] Downloading Kaggle datasets...")
    try:
        kaggle_scraper = KaggleDatasetScraper()
        kaggle_results = kaggle_scraper.download_all_datasets()
        results.update(kaggle_results)
    except Exception as e:
        logger.error(f"Kaggle downloads failed: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Scraping Pipeline Summary")
    logger.info("=" * 60)
    
    for name, result in results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        logger.info(f"{name}: {status}")
        if result:
            logger.info(f"  → {result}")
    
    successful = sum(1 for r in results.values() if r is not None)
    total = len(results)
    logger.info(f"\nTotal: {successful}/{total} sources scraped successfully")
    
    return results


if __name__ == "__main__":
    main()

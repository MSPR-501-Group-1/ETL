"""
Main script to orchestrate all data processors

This file executes all processing pipelines sequentially:
1. Process ExerciseDB exercises
2. Process nutrition data (coming soon)
3. Process user profiles (coming soon)

Usage: python -m src.processors.run_processing
"""

from pathlib import Path
from src.processors.exercise_processor import ExerciseProcessor
from src.processors.gym_members_processor import GymMembersProcessor
from src.utils.logger import setup_logger
from config.settings import RAW_DATA_DIR


def process_exercisedb():
    """
    Process ExerciseDB data
    
    Returns:
        Dict of exported files or None if failed
    """
    logger = setup_logger("ProcessingPipeline")
    logger.info("\n[1/2] Processing ExerciseDB exercises...")
    
    try:
        processor = ExerciseProcessor()
        
        raw_files = list(RAW_DATA_DIR.glob('exercisedb_raw_*.json'))
        
        if not raw_files:
            logger.error("No exercisedb_raw_*.json file found")
            logger.info("💡 Run first: python -m src.scrapers.exercisedb_scraper")
            return None
        
        latest_file = sorted(raw_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        logger.info(f"Source file: {latest_file.name}")
        
        exported = processor.run(latest_file, output_format='both')
        
        return exported
        
    except Exception as e:
        logger.error(f"ExerciseDB processing failed: {e}", exc_info=True)
        return None


def process_gym_members():
    """
    Process Gym Members data from Kaggle
    
    Returns:
        Dict of exported files or None if failed
    """
    logger = setup_logger("ProcessingPipeline")
    logger.info("\n[2/2] Processing Gym Members dataset...")
    
    try:
        processor = GymMembersProcessor()
        
        kaggle_dir = RAW_DATA_DIR / 'kaggle' / 'gym-members-exercise-dataset'
        
        if not kaggle_dir.exists():
            logger.error(f"Kaggle gym members directory not found: {kaggle_dir}")
            logger.info("💡 Run first: python -m src.scrapers.kaggle_scraper")
            return None
        
        csv_files = list(kaggle_dir.glob('*.csv'))
        
        if not csv_files:
            logger.error("No CSV file found in gym members directory")
            return None
        
        latest_file = csv_files[0]
        logger.info(f"Source file: {latest_file.name}")
        
        exported = processor.run(latest_file, output_format='both')
        
        return exported
        
    except Exception as e:
        logger.error(f"Gym Members processing failed: {e}", exc_info=True)
        return None


def main():
    """
    Main function: run all processors in order
    """
    logger = setup_logger("ProcessingPipeline")
    
    logger.info("=" * 60)
    logger.info("Starting Data Processing Pipeline")
    logger.info("=" * 60)
    
    results = {}
    
    exercisedb_result = process_exercisedb()
    results['exercisedb'] = exercisedb_result
    
    gym_members_result = process_gym_members()
    results['gym_members'] = gym_members_result
    
    logger.info("\n" + "=" * 60)
    logger.info("Processing Pipeline Summary")
    logger.info("=" * 60)
    
    for name, result in results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        logger.info(f"{name}: {status}")
        
        if result and isinstance(result, dict):
            for format_type, filepath in result.items():
                logger.info(f"  → {format_type.upper()}: {filepath}")
    
    successful = sum(1 for r in results.values() if r is not None)
    total = len(results)
    logger.info(f"\nTotal: {successful}/{total} sources processed successfully")
    
    return results


if __name__ == "__main__":
    main()

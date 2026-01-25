"""
Scraper to download datasets from Kaggle using their official API

IMPORTANT: Requires Kaggle authentication
Required configuration:
1. Create account on kaggle.com
2. Get your API token from https://www.kaggle.com/account
3. Place kaggle.json file in ~/.kaggle/ (Mac/Linux) or %USERPROFILE%\.kaggle\ (Windows)

This scraper uses Kaggle CLI to download datasets
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional
from config.settings import RAW_DATA_DIR
from src.utils.logger import setup_logger


class KaggleDatasetScraper:
    """
    Class to automatically download datasets from Kaggle
    
    Features:
    - Uses Kaggle CLI (official command-line tool)
    - Downloads and unzips files automatically
    - Organizes datasets in subfolders
    
    Prerequisites:
    1. Install kaggle CLI: pip install kaggle
    2. Configure credentials (kaggle.json file with your API key)
    3. File must be in: ~/.kaggle/kaggle.json
    """
    
    def __init__(self):
        """
        Initialize scraper and verify configuration
        """
        self.logger = setup_logger(self.__class__.__name__)
        self.check_kaggle_cli()
    
    def check_kaggle_cli(self) -> bool:
        """
        Check if Kaggle CLI is installed and available on system
        
        Returns:
            bool: True if kaggle CLI is found, False otherwise
        """
        if not shutil.which('kaggle'):
            self.logger.warning("Kaggle CLI not found. Install with: pip install kaggle")
            return False
        return True
    
    def download_dataset(self, dataset_slug: str, output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Download dataset from Kaggle using command line
        
        Dataset slug is unique identifier on Kaggle.
        Found in URL: kaggle.com/datasets/USERNAME/DATASET-NAME
        
        Args:
            dataset_slug: Kaggle identifier (format: 'username/dataset-name')
            output_dir: Destination folder (created automatically if not exists)
            
        Returns:
            Path: Path to folder containing downloaded files
            None: If download fails
            
        Example:
            download_dataset('adilshamim8/daily-food-and-nutrition-dataset')
        """
        if output_dir is None:
            dataset_name = dataset_slug.split('/')[-1]
            output_dir = RAW_DATA_DIR / 'kaggle' / dataset_name
        
        output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Downloading Kaggle dataset: {dataset_slug}")
        
        try:
            result = subprocess.run(
                ['kaggle', 'datasets', 'download', '-d', dataset_slug, '-p', str(output_dir), '--unzip'],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"Download successful to {output_dir}")
            self.logger.debug(result.stdout)
            return output_dir
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Download failed: {e.stderr}")
            return None
        except FileNotFoundError:
            self.logger.error("Kaggle CLI not found. Install with: pip install kaggle")
            return None
    
    def download_nutrition_dataset(self) -> Optional[Path]:
        """
        Download Daily Food & Nutrition Dataset
        """
        return self.download_dataset('adilshamim8/daily-food-and-nutrition-dataset')
    
    def download_diet_recommendations_dataset(self) -> Optional[Path]:
        """
        Download Diet Recommendations Dataset
        """
        return self.download_dataset('ziya07/diet-recommendations-dataset')
    
    def download_gym_members_dataset(self) -> Optional[Path]:
        """
        Download Gym Members Exercise Dataset
        """
        return self.download_dataset('valakhorasani/gym-members-exercise-dataset')
    
    def download_fitness_tracker_dataset(self) -> Optional[Path]:
        """
        Download Fitness Tracker Dataset
        """
        return self.download_dataset('nadeemajeedch/fitness-tracker-dataset')
    
    def download_all_datasets(self) -> Dict[str, Optional[Path]]:
        """
        Download all required datasets for the project
        
        Returns:
            Dictionary with dataset names and their paths
        """
        self.logger.info("Starting download of all Kaggle datasets")
        
        datasets = {
            'nutrition': self.download_nutrition_dataset(),
            'diet_recommendations': self.download_diet_recommendations_dataset(),
            'gym_members': self.download_gym_members_dataset(),
            'fitness_tracker': self.download_fitness_tracker_dataset()
        }
        
        successful = sum(1 for path in datasets.values() if path is not None)
        self.logger.info(f"Downloaded {successful}/{len(datasets)} datasets successfully")
        
        return datasets


if __name__ == "__main__":
    # Test the scraper
    scraper = KaggleDatasetScraper()
    
    # Download a single dataset
    print("Testing single dataset download...")
    result = scraper.download_nutrition_dataset()
    
    if result:
        print(f"✅ Dataset downloaded to: {result}")
    else:
        print("❌ Download failed - check Kaggle API configuration")

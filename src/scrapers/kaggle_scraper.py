"""
Scraper pour télécharger des datasets depuis Kaggle en utilisant leur API officielle

IMPORTANT : Nécessite une authentification Kaggle
Configuration requise :
1. Créer un compte sur kaggle.com
2. Obtenir votre token API depuis https://www.kaggle.com/account
3. Placer le fichier kaggle.json dans ~/.kaggle/ (Mac/Linux) ou %USERPROFILE%\.kaggle\ (Windows)

Ce scraper utilise la ligne de commande Kaggle (CLI) pour télécharger les datasets
"""

import subprocess  # Pour exécuter des commandes système (kaggle CLI)
import shutil  # Pour vérifier si des programmes sont installés
from pathlib import Path  # Pour manipuler les chemins de fichiers
from typing import Optional  # Pour définir les types de retour
from config.settings import RAW_DATA_DIR  # Dossier où sauvegarder les données
from src.utils.logger import setup_logger  # Pour les logs


class KaggleDatasetScraper:
    """
    Classe pour télécharger automatiquement des datasets depuis Kaggle
    
    Fonctionnement:
    - Utilise la CLI Kaggle (outil en ligne de commande officiel)
    - Télécharge et dézippe automatiquement les fichiers
    - Organise les datasets dans des sous-dossiers
    
    Prérequis techniques:
    1. Installer kaggle CLI : pip install kaggle
    2. Configurer les credentials (fichier kaggle.json avec votre clé API)
    3. Le fichier doit être dans : ~/.kaggle/kaggle.json
    """
    
    def __init__(self):
        """
        Constructeur : initialise le scraper et vérifie la configuration
        """
        # Créer le système de logs
        self.logger = setup_logger(self.__class__.__name__)
        
        # Vérifier que la CLI Kaggle est installée et accessible
        self.check_kaggle_cli()
    
    def check_kaggle_cli(self) -> bool:
        """
        Vérifier si la CLI Kaggle est installée et disponible sur le système
        
        Cette fonction cherche la commande 'kaggle' dans le PATH système.
        Si elle n'est pas trouvée, affiche un avertissement.
        
        Returns:
            bool: True si kaggle CLI est trouvée, False sinon
        """
        # shutil.which() cherche un programme dans le PATH système
        # Équivalent de taper 'where kaggle' dans le terminal Windows
        if not shutil.which('kaggle'):
            self.logger.warning("CLI Kaggle non trouvée. Installez avec : pip install kaggle")
            return False
        return True
    
    def download_dataset(self, dataset_slug: str, output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Télécharger un dataset depuis Kaggle en utilisant la ligne de commande
        
        Le dataset_slug est l'identifiant unique du dataset sur Kaggle.
        On le trouve dans l'URL : kaggle.com/datasets/USERNAME/DATASET-NAME
        
        Args:
            dataset_slug: Identifiant Kaggle (format: 'username/dataset-name')
            output_dir: Dossier de destination (créé automatiquement si inexistant)
            
        Returns:
            Path: Chemin vers le dossier contenant les fichiers téléchargés
            None: Si le téléchargement échoue
            
        Exemple:
            download_dataset('adilshamim8/daily-food-and-nutrition-dataset')
        """
        # Si aucun dossier de destination n'est spécifié, en créer un automatiquement
        # Structure: data/raw/kaggle/NOM-DU-DATASET/
        if output_dir is None:
            # Extraire le nom du dataset depuis le slug (partie après le /)
            dataset_name = dataset_slug.split('/')[-1]
            output_dir = RAW_DATA_DIR / 'kaggle' / dataset_name
        
        # Créer le dossier (et les dossiers parents) s'il n'existe pas
        # exist_ok=True évite une erreur si le dossier existe déjà
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Téléchargement du dataset Kaggle : {dataset_slug}")
        
        try:
            # Exécuter la commande kaggle CLI dans un sous-processus
            # Équivalent de taper: kaggle datasets download -d SLUG -p DOSSIER --unzip
            result = subprocess.run(
                ['kaggle', 'datasets', 'download', '-d', dataset_slug, '-p', str(output_dir), '--unzip'],
                capture_output=True,  # Capturer la sortie (stdout et stderr)
                text=True,            # Retourner du texte (pas des bytes)
                check=True            # Lever une erreur si la commande échoue
            )
            
            self.logger.info(f"Téléchargement réussi dans {output_dir}")
            self.logger.debug(result.stdout)  # Logger la sortie détaillée
            return output_dir
            
        except subprocess.CalledProcessError as e:
            # Erreur lors de l'exécution de la commande (credentials invalides, dataset introuvable...)
            self.logger.error(f"Échec du téléchargement : {e.stderr}")
            return None
        except FileNotFoundError:
            # La commande 'kaggle' n'a pas été trouvée (pas installée)
            self.logger.error("CLI Kaggle non trouvée. Installez avec : pip install kaggle")
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

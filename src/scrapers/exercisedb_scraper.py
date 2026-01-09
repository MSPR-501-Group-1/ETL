"""
Scraper pour récupérer les données d'exercices depuis ExerciseDB (GitHub)
Source: https://github.com/yuhonas/free-exercise-db

Ce module permet de télécharger automatiquement une liste d'exercices sportifs
avec leurs caractéristiques (muscles ciblés, équipement, instructions, etc.)
"""

import requests  # Bibliothèque pour faire des requêtes HTTP (télécharger des données depuis internet)
import time  # Pour gérer les dates et heures
from pathlib import Path  # Pour manipuler les chemins de fichiers
from typing import List, Dict, Optional  # Pour définir les types de données (aide au débogage)
from config.settings import RAW_DATA_DIR, SCRAPING_CONFIG  # Configuration du projet
from src.utils.logger import setup_logger  # Pour enregistrer les logs (traces d'exécution)
from src.utils.file_handler import save_to_json, generate_filename  # Pour sauvegarder les fichiers


class ExerciseDBScraper:
    """
    Classe principale pour récupérer les exercices depuis ExerciseDB
    
    Fonctionnement:
    1. Se connecte à l'URL GitHub qui contient les données JSON
    2. Télécharge la liste complète des exercices
    3. Extrait les métadonnées (catégories, équipements, etc.)
    4. Sauvegarde tout dans un fichier JSON local
    """
    
    # URL de base où se trouvent les données (fichier JSON public sur GitHub)
    BASE_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
    
    def __init__(self):
        """
        Constructeur : initialise le scraper au démarrage
        
        Crée:
        - Un logger pour tracer l'exécution (enregistrer ce qui se passe)
        - Une session HTTP pour faire les requêtes web
        - Configure un User-Agent (s'identifier comme un navigateur web)
        """
        # Créer un système de logs avec le nom de la classe
        self.logger = setup_logger(self.__class__.__name__)
        
        # Créer une session HTTP (connexion réutilisable pour télécharger des données)
        self.session = requests.Session()
        
        # Définir un User-Agent (se faire passer pour un navigateur Chrome sur Windows)
        # Certains sites bloquent les requêtes sans User-Agent
        self.session.headers.update({
            'User-Agent': SCRAPING_CONFIG['user_agent']
        })
        
    def fetch_exercises(self) -> Optional[List[Dict]]:
        """
        ÉTAPE 1 : Télécharger tous les exercices depuis l'URL GitHub
        
        Processus:
        1. Fait une requête HTTP GET vers l'URL (comme ouvrir une page web)
        2. Vérifie que la requête a réussi (code 200)
        3. Convertit la réponse JSON en liste Python
        
        Returns:
            List[Dict]: Liste de dictionnaires contenant les exercices
            None: Si le téléchargement échoue
        """
        # Enregistrer dans les logs qu'on commence le téléchargement
        self.logger.info(f"Téléchargement des exercices depuis {self.BASE_URL}")
        
        try:
            # Faire une requête GET (télécharger les données depuis l'URL)
            # timeout = temps maximum d'attente avant abandon (30 secondes par défaut)
            response = self.session.get(
                self.BASE_URL,
                timeout=SCRAPING_CONFIG['timeout']
            )
            
            # Vérifier que la requête a réussi (lance une erreur si code != 200)
            response.raise_for_status()
            
            # Convertir la réponse JSON en objet Python (liste de dictionnaires)
            exercises = response.json()
            
            # Logger le succès avec le nombre d'exercices récupérés
            self.logger.info(f"Succès : {len(exercises)} exercices téléchargés")
            return exercises
            
        except requests.exceptions.RequestException as e:
            # Si une erreur se produit (pas d'internet, URL invalide, timeout...)
            self.logger.error(f"Échec du téléchargement : {e}")
            return None
    
    def fetch_exercise_categories(self, exercises: List[Dict]) -> Dict[str, List[str]]:
        """
        ÉTAPE 2 : Extraire les catégories uniques depuis la liste d'exercices
        
        Cette fonction parcourt tous les exercices et crée des listes de:
        - Groupes musculaires (bodyParts) : biceps, triceps, abdos, etc.
        - Équipements (equipment) : haltères, barres, poids du corps, etc.
        - Types d'exercice (targets) : cardio, force, stretching, etc.
        
        Args:
            exercises: Liste des exercices téléchargés
            
        Returns:
            Dict: Dictionnaire avec 3 clés (bodyParts, equipment, targets)
                  chacune contenant une liste triée de valeurs uniques
        """
        # Créer 3 ensembles (set) pour stocker les valeurs uniques
        # Un set = collection qui n'accepte pas les doublons
        categories = {
            'bodyParts': set(),    # Groupes musculaires
            'equipment': set(),    # Types d'équipement
            'targets': set()       # Catégories d'exercices
        }
        
        # Parcourir chaque exercice pour extraire ses caractéristiques
        for exercise in exercises:
            # Vérifier si l'exercice a des muscles primaires définis
            if 'primaryMuscles' in exercise and exercise['primaryMuscles']:
                # Ajouter tous les muscles au set (update = ajouter plusieurs éléments)
                categories['bodyParts'].update(exercise['primaryMuscles'])
            
            # Vérifier si l'exercice a un équipement défini
            if 'equipment' in exercise and exercise['equipment']:
                # Ajouter l'équipement au set (add = ajouter un élément)
                categories['equipment'].add(exercise['equipment'])
            
            # Vérifier si l'exercice a une catégorie définie
            if 'category' in exercise and exercise['category']:
                # Ajouter la catégorie au set
                categories['targets'].add(exercise['category'])
        
        # Convertir les sets en listes triées et filtrer les valeurs None
        # Compréhension de dictionnaire : {clé: valeur transformée pour chaque clé, valeur}
        return {key: sorted([v for v in values if v is not None]) for key, values in categories.items()}
    
    def save_data(self, exercises: List[Dict], filename: Optional[str] = None) -> Path:
        """
        ÉTAPE 3 : Sauvegarder les données dans un fichier JSON
        
        Crée un fichier JSON avec toutes les données récupérées.
        Le nom du fichier inclut un timestamp pour tracer les versions.
        
        Args:
            exercises: Données à sauvegarder (dict avec metadata + exercises)
            filename: Nom du fichier (optionnel, auto-généré si non fourni)
            
        Returns:
            Path: Chemin complet vers le fichier créé
        """
        # Si aucun nom de fichier n'est fourni, en générer un automatiquement
        # Format: exercisedb_raw_YYYYMMDD_HHMMSS.json
        if filename is None:
            filename = generate_filename('exercisedb_raw')
        
        # Construire le chemin complet : dossier data/raw/ + nom du fichier
        filepath = RAW_DATA_DIR / filename
        
        # Sauvegarder les données au format JSON (format texte lisible)
        save_to_json(exercises, filepath)
        
        # Logger l'emplacement du fichier sauvegardé
        self.logger.info(f"Sauvegarde de {len(exercises)} exercices dans {filepath}")
        return filepath
    
    def run(self) -> Optional[Path]:
        """
        MÉTHODE PRINCIPALE : Exécute le pipeline complet de scraping
        
        Cette méthode orchestre toutes les étapes dans l'ordre:
        1. Télécharger les exercices depuis l'URL
        2. Extraire les métadonnées (catégories)
        3. Structurer les données avec les métadonnées
        4. Sauvegarder dans un fichier JSON
        
        Returns:
            Path: Chemin vers le fichier créé
            None: Si une erreur s'est produite
        """
        self.logger.info("Démarrage du pipeline de scraping ExerciseDB")
        
        # ÉTAPE 1 : Télécharger les données depuis GitHub
        exercises = self.fetch_exercises()
        if exercises is None:
            # Si le téléchargement échoue, arrêter le processus
            self.logger.error("Échec du scraping - aucune donnée récupérée")
            return None
        
        # ÉTAPE 2 : Extraire les catégories uniques (muscles, équipements, types)
        categories = self.fetch_exercise_categories(exercises)
        self.logger.info(f"Catégories trouvées : {categories}")
        
        # ÉTAPE 3 : Préparer la structure finale avec métadonnées + données
        # Cette structure facilite la traçabilité et l'analyse ultérieure
        data = {
            'metadata': {
                'source': 'ExerciseDB',
                'url': self.BASE_URL,
                'total_exercises': len(exercises),
                'categories': categories,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')  # Date et heure du scraping
            },
            'exercises': exercises  # Liste complète des exercices
        }
        
        # ÉTAPE 4 : Sauvegarder dans un fichier JSON
        filepath = self.save_data(data)
        
        self.logger.info("Scraping ExerciseDB terminé avec succès")
        return filepath


if __name__ == "__main__":
    # Test the scraper
    scraper = ExerciseDBScraper()
    result = scraper.run()
    
    if result:
        print(f"✅ Data successfully saved to: {result}")
    else:
        print("❌ Scraping failed")

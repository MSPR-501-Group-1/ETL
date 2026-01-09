"""
Script principal pour exécuter tous les scrapers de manière séquentielle

Ce fichier orchestre l'ensemble du processus de collecte de données :
1. Télécharge les exercices depuis ExerciseDB (GitHub)
2. Télécharge les 4 datasets depuis Kaggle
3. Affiche un résumé des succès/échecs

Usage : python -m src.scrapers.run_scraping
"""

from pathlib import Path  # Pour manipuler les chemins
from src.scrapers.exercisedb_scraper import ExerciseDBScraper  # Scraper GitHub
from src.scrapers.kaggle_scraper import KaggleDatasetScraper  # Scraper Kaggle
from src.utils.logger import setup_logger  # Système de logs


def main():
    """
    Fonction principale : lance tous les scrapers dans l'ordre
    
    Processus:
    1. Initialise le système de logs
    2. Exécute le scraper ExerciseDB
    3. Exécute les téléchargements Kaggle
    4. Affiche un résumé final
    """
    # Créer un logger pour ce pipeline
    logger = setup_logger("ScrapingPipeline")
    
    # Afficher un en-tête visuel dans les logs
    logger.info("=" * 60)
    logger.info("Démarrage du Pipeline ETL de Scraping")
    logger.info("=" * 60)
    
    # Dictionnaire pour stocker les résultats de chaque scraper
    # Clé = nom du dataset, Valeur = chemin du fichier ou None si échec
    results = {}
    
    # ========================================
    # ÉTAPE 1 : Scraper ExerciseDB depuis GitHub
    # ========================================
    logger.info("\n[1/2] Téléchargement des exercices depuis ExerciseDB (GitHub)...")
    try:
        # Créer une instance du scraper ExerciseDB
        exercisedb_scraper = ExerciseDBScraper()
        # Exécuter le scraping complet (téléchargement + sauvegarde)
        results['exercisedb'] = exercisedb_scraper.run()
    except Exception as e:
        # Si une erreur se produit, la logger et continuer avec les autres sources
        logger.error(f"Échec du scraping ExerciseDB : {e}")
        results['exercisedb'] = None
    
    # ========================================
    # ÉTAPE 2 : Télécharger les datasets Kaggle
    # ========================================
    logger.info("\n[2/2] Téléchargement des datasets Kaggle...")
    try:
        # Créer une instance du scraper Kaggle
        kaggle_scraper = KaggleDatasetScraper()
        # Télécharger tous les datasets du projet (nutrition, gym, fitness...)
        kaggle_results = kaggle_scraper.download_all_datasets()
        # Fusionner les résultats Kaggle avec le résultat ExerciseDB
        results.update(kaggle_results)
    except Exception as e:
        # Si Kaggle échoue (pas de credentials, pas d'internet...), logger l'erreur
        logger.error(f"Échec des téléchargements Kaggle : {e}")
    
    # ========================================
    # ÉTAPE 3 : Afficher le résumé final
    # ========================================
    logger.info("\n" + "=" * 60)
    logger.info("Résumé du Pipeline de Scraping")
    logger.info("=" * 60)
    
    # Parcourir tous les résultats et afficher le statut
    for name, result in results.items():
        # Icône ✅ si succès (result != None), ❌ si échec
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        logger.info(f"{name}: {status}")
        # Si succès, afficher le chemin du fichier/dossier créé
        if result:
            logger.info(f"  → {result}")
    
    # Calculer le nombre de sources téléchargées avec succès
    successful = sum(1 for r in results.values() if r is not None)
    total = len(results)
    logger.info(f"\nTotal : {successful}/{total} sources scrapées avec succès")
    
    # Retourner le dictionnaire de résultats pour utilisation ultérieure
    return results


if __name__ == "__main__":
    main()

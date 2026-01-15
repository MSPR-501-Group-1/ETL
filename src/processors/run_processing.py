"""
Script principal pour orchestrer tous les processeurs de données

Ce fichier permet d'exécuter tous les pipelines de traitement de manière séquentielle:
1. Traitement des exercices ExerciseDB
2. Traitement des données nutritionnelles (à venir)
3. Traitement des profils utilisateurs (à venir)

Usage : python -m src.processors.run_processing
"""

from pathlib import Path
from src.processors.exercise_processor import ExerciseProcessor
from src.utils.logger import setup_logger
from config.settings import RAW_DATA_DIR


def process_exercisedb():
    """
    Traite les données ExerciseDB
    
    Returns:
        Dict des fichiers exportés ou None si échec
    """
    logger = setup_logger("ProcessingPipeline")
    logger.info("\n[1/1] Traitement des exercices ExerciseDB...")
    
    try:
        processor = ExerciseProcessor()
        
        # Trouver le fichier brut le plus récent
        raw_files = list(RAW_DATA_DIR.glob('exercisedb_raw_*.json'))
        
        if not raw_files:
            logger.error("Aucun fichier exercisedb_raw_*.json trouvé")
            logger.info("💡 Exécutez d'abord: python -m src.scrapers.exercisedb_scraper")
            return None
        
        # Prendre le fichier le plus récent
        latest_file = sorted(raw_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        logger.info(f"Fichier source: {latest_file.name}")
        
        # Exécuter le traitement
        exported = processor.run(latest_file, output_format='both')
        
        return exported
        
    except Exception as e:
        logger.error(f"Échec du traitement ExerciseDB : {e}", exc_info=True)
        return None


def main():
    """
    Fonction principale : lance tous les processeurs dans l'ordre
    """
    logger = setup_logger("ProcessingPipeline")
    
    # Afficher un en-tête visuel
    logger.info("=" * 60)
    logger.info("Démarrage du Pipeline de Traitement de Données")
    logger.info("=" * 60)
    
    # Dictionnaire pour stocker les résultats
    results = {}
    
    # ========================================
    # ÉTAPE 1 : Traiter les exercices ExerciseDB
    # ========================================
    exercisedb_result = process_exercisedb()
    results['exercisedb'] = exercisedb_result
    
    # ========================================
    # TODO : Ajouter d'autres processeurs ici
    # ========================================
    # results['nutrition'] = process_nutrition()
    # results['gym_members'] = process_gym_members()
    # results['fitness_tracker'] = process_fitness_tracker()
    
    # ========================================
    # Afficher le résumé final
    # ========================================
    logger.info("\n" + "=" * 60)
    logger.info("Résumé du Pipeline de Traitement")
    logger.info("=" * 60)
    
    for name, result in results.items():
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        logger.info(f"{name}: {status}")
        
        if result and isinstance(result, dict):
            for format_type, filepath in result.items():
                logger.info(f"  → {format_type.upper()}: {filepath}")
    
    # Calculer le nombre de sources traitées avec succès
    successful = sum(1 for r in results.values() if r is not None)
    total = len(results)
    logger.info(f"\nTotal : {successful}/{total} sources traitées avec succès")
    
    return results


if __name__ == "__main__":
    main()

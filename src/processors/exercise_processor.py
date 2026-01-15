"""
Processor pour nettoyer et transformer les données d'exercices ExerciseDB

Ce module applique les transformations suivantes:
1. Validation de la structure des données
2. Nettoyage des champs (normalisation, gestion des valeurs nulles)
3. Enrichissement des données (calcul de scores, catégorisation)
4. Déduplication et cohérence
5. Export au format exploitable
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import setup_logger
from src.utils.file_handler import save_to_json, save_to_csv, load_from_json
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR


class ExerciseProcessor:
    """
    Processeur pour nettoyer et transformer les données d'exercices
    
    Pipeline de transformation:
    1. Chargement des données brutes
    2. Validation de la structure
    3. Nettoyage et normalisation
    4. Enrichissement
    5. Export des données propres
    """
    
    def __init__(self):
        """Initialise le processeur et le système de logs"""
        self.logger = setup_logger(self.__class__.__name__)
        self.stats = {
            'total_exercises': 0,
            'valid_exercises': 0,
            'invalid_exercises': 0,
            'duplicates_removed': 0,
            'fields_cleaned': 0
        }
    
    def load_raw_data(self, filepath: Path) -> Tuple[Dict, pd.DataFrame]:
        """
        Charge les données brutes depuis un fichier JSON
        
        Args:
            filepath: Chemin vers le fichier JSON brut
            
        Returns:
            Tuple contenant (metadata, DataFrame des exercices)
        """
        self.logger.info(f"Chargement des données depuis {filepath}")
        
        # Charger le JSON complet
        raw_data = load_from_json(filepath)
        
        # Extraire les métadonnées et les exercices
        metadata = raw_data.get('metadata', {})
        exercises = raw_data.get('exercises', [])
        
        # Convertir en DataFrame pour faciliter la manipulation
        df = pd.DataFrame(exercises)
        
        self.stats['total_exercises'] = len(df)
        self.logger.info(f"{len(df)} exercices chargés")
        
        return metadata, df
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valide la structure et la cohérence des données
        
        Règles de validation:
        - Champs obligatoires: name, id, category, equipment, primaryMuscles
        - Format correct pour les listes et les chaînes
        - Valeurs cohérentes (level, category, equipment dans listes autorisées)
        
        Args:
            df: DataFrame des exercices
            
        Returns:
            DataFrame avec uniquement les exercices valides
        """
        self.logger.info("Validation des données...")
        
        initial_count = len(df)
        
        # 1. Vérifier les champs obligatoires
        required_fields = ['name', 'id', 'category', 'equipment', 'primaryMuscles']
        
        for field in required_fields:
            if field not in df.columns:
                self.logger.warning(f"Champ obligatoire manquant: {field}")
                df[field] = None
        
        # 2. Supprimer les lignes avec des champs obligatoires vides
        mask = df['name'].notna() & df['id'].notna()
        df = df[mask].copy()
        
        # 3. Valider les listes (primaryMuscles, secondaryMuscles, instructions)
        for list_field in ['primaryMuscles', 'secondaryMuscles', 'instructions']:
            if list_field in df.columns:
                # Convertir en liste vide si None
                df[list_field] = df[list_field].apply(
                    lambda x: x if isinstance(x, list) else []
                )
        
        # 4. Valider les niveaux de difficulté
        valid_levels = ['beginner', 'intermediate', 'expert']
        df['level'] = df['level'].apply(
            lambda x: x if x in valid_levels else 'intermediate'
        )
        
        # 5. Valider les catégories
        valid_categories = [
            'cardio', 'olympic weightlifting', 'plyometrics',
            'powerlifting', 'strength', 'stretching', 'strongman'
        ]
        df['category'] = df['category'].apply(
            lambda x: x if x in valid_categories else 'strength'
        )
        
        self.stats['valid_exercises'] = len(df)
        self.stats['invalid_exercises'] = initial_count - len(df)
        
        self.logger.info(
            f"Validation terminée: {self.stats['valid_exercises']} valides, "
            f"{self.stats['invalid_exercises']} rejetés"
        )
        
        return df
    
    def clean_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie et normalise les champs textuels
        
        Opérations:
        - Trim des espaces
        - Normalisation de la casse
        - Suppression des caractères spéciaux indésirables
        
        Args:
            df: DataFrame des exercices
            
        Returns:
            DataFrame avec champs texte nettoyés
        """
        self.logger.info("Nettoyage des champs textuels...")
        
        # Champs à nettoyer
        text_fields = ['name', 'equipment', 'force', 'mechanic', 'category']
        
        for field in text_fields:
            if field in df.columns:
                # Trim et normalisation
                df[field] = df[field].apply(
                    lambda x: x.strip().lower() if isinstance(x, str) else x
                )
                self.stats['fields_cleaned'] += 1
        
        return df
    
    def normalize_muscle_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalise et enrichit les groupes musculaires
        
        Opérations:
        - Standardisation des noms de muscles
        - Ajout d'une colonne 'all_muscles' combinant primaires + secondaires
        - Comptage du nombre de muscles ciblés
        
        Args:
            df: DataFrame des exercices
            
        Returns:
            DataFrame enrichi
        """
        self.logger.info("Normalisation des groupes musculaires...")
        
        # Mapping pour standardiser les noms de muscles
        muscle_mapping = {
            'abs': 'abdominals',
            'quads': 'quadriceps',
            'lats': 'lats',
            'traps': 'trapezius',
        }
        
        def normalize_muscle_list(muscles):
            """Normalise une liste de muscles"""
            if not isinstance(muscles, list):
                return []
            return [muscle_mapping.get(m.lower(), m.lower()) for m in muscles]
        
        # Normaliser les listes
        df['primaryMuscles'] = df['primaryMuscles'].apply(normalize_muscle_list)
        df['secondaryMuscles'] = df['secondaryMuscles'].apply(normalize_muscle_list)
        
        # Créer une colonne combinée de tous les muscles
        df['all_muscles'] = df.apply(
            lambda row: list(set(row['primaryMuscles'] + row['secondaryMuscles'])),
            axis=1
        )
        
        # Compter le nombre de muscles ciblés
        df['muscle_count'] = df['all_muscles'].apply(len)
        
        # Déterminer si c'est un exercice composé ou d'isolation
        df['exercise_type'] = df['muscle_count'].apply(
            lambda x: 'compound' if x > 2 else 'isolation'
        )
        
        return df
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrichit les données avec des champs calculés
        
        Ajouts:
        - Difficulté numérique (1-3)
        - Score de complexité basé sur les instructions
        - Nécessite équipement (booléen)
        - Catégorie principale de mouvement
        
        Args:
            df: DataFrame des exercices
            
        Returns:
            DataFrame enrichi
        """
        self.logger.info("Enrichissement des données...")
        
        # 1. Convertir le niveau en score numérique
        level_scores = {'beginner': 1, 'intermediate': 2, 'expert': 3}
        df['difficulty_score'] = df['level'].map(level_scores)
        
        # 2. Calculer un score de complexité basé sur le nombre d'instructions
        df['instruction_count'] = df['instructions'].apply(len)
        df['complexity_score'] = df.apply(
            lambda row: row['difficulty_score'] + (row['instruction_count'] / 10),
            axis=1
        )
        
        # 3. Déterminer si l'exercice nécessite de l'équipement
        df['requires_equipment'] = df['equipment'].apply(
            lambda x: x not in ['body only', 'none', None]
        )
        
        # 4. Catégoriser par type de mouvement
        push_indicators = ['push', 'press', 'chest', 'triceps', 'shoulders']
        pull_indicators = ['pull', 'row', 'back', 'biceps', 'lats']
        
        def categorize_movement(row):
            """Catégorise le type de mouvement"""
            name_lower = row['name'].lower() if isinstance(row['name'], str) else ''
            
            if any(word in name_lower for word in push_indicators):
                return 'push'
            elif any(word in name_lower for word in pull_indicators):
                return 'pull'
            elif row['category'] in ['cardio', 'stretching']:
                return row['category']
            else:
                return 'other'
        
        df['movement_type'] = df.apply(categorize_movement, axis=1)
        
        return df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les exercices en double
        
        Stratégie:
        - Identifier les doublons par 'id' ou 'name'
        - Conserver la version la plus complète
        
        Args:
            df: DataFrame des exercices
            
        Returns:
            DataFrame dédupliqué
        """
        self.logger.info("Suppression des doublons...")
        
        initial_count = len(df)
        
        # Supprimer les doublons basés sur l'ID (priorité absolue)
        df = df.drop_duplicates(subset=['id'], keep='first')
        
        # Supprimer les doublons basés sur le nom (cas où ID différent mais nom identique)
        df = df.drop_duplicates(subset=['name'], keep='first')
        
        self.stats['duplicates_removed'] = initial_count - len(df)
        
        self.logger.info(f"{self.stats['duplicates_removed']} doublons supprimés")
        
        return df
    
    def add_metadata_columns(self, df: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        """
        Ajoute des colonnes de métadonnées pour la traçabilité
        
        Args:
            df: DataFrame des exercices
            metadata: Dictionnaire de métadonnées
            
        Returns:
            DataFrame avec métadonnées
        """
        df['data_source'] = metadata.get('source', 'ExerciseDB')
        df['scraped_at'] = metadata.get('scraped_at', datetime.now().isoformat())
        df['processed_at'] = datetime.now().isoformat()
        
        return df
    
    def get_processing_stats(self) -> Dict:
        """
        Retourne les statistiques de traitement
        
        Returns:
            Dictionnaire des statistiques
        """
        return self.stats
    
    def export_processed_data(
        self,
        df: pd.DataFrame,
        metadata: Dict,
        output_format: str = 'both'
    ) -> Dict[str, Path]:
        """
        Exporte les données traitées en JSON et/ou CSV
        
        Args:
            df: DataFrame des exercices traités
            metadata: Métadonnées à inclure
            output_format: 'json', 'csv' ou 'both'
            
        Returns:
            Dictionnaire des chemins des fichiers créés
        """
        self.logger.info(f"Export des données au format {output_format}...")
        
        # Créer le dossier de sortie
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exported_files = {}
        
        # Export JSON
        if output_format in ['json', 'both']:
            json_filename = f'exercises_processed_{timestamp}.json'
            json_filepath = PROCESSED_DATA_DIR / json_filename
            
            # Préparer les données avec métadonnées
            output_data = {
                'metadata': {
                    **metadata,
                    'processing_stats': self.stats,
                    'processed_at': datetime.now().isoformat(),
                    'total_processed_exercises': len(df)
                },
                'exercises': df.to_dict('records')
            }
            
            save_to_json(output_data, json_filepath)
            exported_files['json'] = json_filepath
            self.logger.info(f"JSON sauvegardé: {json_filepath}")
        
        # Export CSV
        if output_format in ['csv', 'both']:
            csv_filename = f'exercises_processed_{timestamp}.csv'
            csv_filepath = PROCESSED_DATA_DIR / csv_filename
            
            # Préparer le DataFrame pour CSV (aplatir les listes)
            df_csv = df.copy()
            
            # Convertir les listes en chaînes séparées par des virgules
            list_columns = ['primaryMuscles', 'secondaryMuscles', 'all_muscles', 'instructions', 'images']
            for col in list_columns:
                if col in df_csv.columns:
                    df_csv[col] = df_csv[col].apply(
                        lambda x: '|'.join(x) if isinstance(x, list) else ''
                    )
            
            save_to_csv(df_csv, csv_filepath)
            exported_files['csv'] = csv_filepath
            self.logger.info(f"CSV sauvegardé: {csv_filepath}")
        
        return exported_files
    
    def run(self, input_file: Path, output_format: str = 'both') -> Dict[str, Path]:
        """
        Exécute le pipeline complet de traitement
        
        Pipeline:
        1. Chargement des données brutes
        2. Validation
        3. Nettoyage
        4. Normalisation
        5. Enrichissement
        6. Déduplication
        7. Export
        
        Args:
            input_file: Chemin vers le fichier JSON brut
            output_format: Format d'export ('json', 'csv', 'both')
            
        Returns:
            Dictionnaire des fichiers exportés
        """
        self.logger.info("=" * 60)
        self.logger.info("Démarrage du pipeline de traitement ExerciseDB")
        self.logger.info("=" * 60)
        
        try:
            # 1. Chargement
            metadata, df = self.load_raw_data(input_file)
            
            # 2. Validation
            df = self.validate_data(df)
            
            # 3. Nettoyage
            df = self.clean_text_fields(df)
            
            # 4. Normalisation des muscles
            df = self.normalize_muscle_groups(df)
            
            # 5. Enrichissement
            df = self.enrich_data(df)
            
            # 6. Déduplication
            df = self.remove_duplicates(df)
            
            # 7. Ajout métadonnées
            df = self.add_metadata_columns(df, metadata)
            
            # 8. Export
            exported_files = self.export_processed_data(df, metadata, output_format)
            
            # Afficher les statistiques
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Statistiques de traitement")
            self.logger.info("=" * 60)
            for key, value in self.stats.items():
                self.logger.info(f"{key}: {value}")
            
            self.logger.info("\n✅ Pipeline de traitement terminé avec succès")
            
            return exported_files
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du traitement : {e}", exc_info=True)
            raise


# Script exécutable
if __name__ == "__main__":
    # Exemple d'utilisation
    processor = ExerciseProcessor()
    
    # Utiliser le fichier le plus récent dans raw/
    raw_files = list(RAW_DATA_DIR.glob('exercisedb_raw_*.json'))
    
    if raw_files:
        # Trier par date de modification (le plus récent en premier)
        latest_file = sorted(raw_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        
        print(f"\n📁 Fichier source: {latest_file.name}")
        
        # Exécuter le traitement
        exported = processor.run(latest_file, output_format='both')
        
        print("\n📤 Fichiers exportés:")
        for format_type, filepath in exported.items():
            print(f"  {format_type.upper()}: {filepath}")
    else:
        print("❌ Aucun fichier brut trouvé dans data/raw/")
        print("💡 Exécutez d'abord: python -m src.scrapers.exercisedb_scraper")

"""
Tests unitaires pour le module ExerciseProcessor

Ce fichier teste toutes les fonctions de transformation et de validation
du processeur d'exercices.
"""

import pytest
import pandas as pd
from pathlib import Path
from src.processors.exercise_processor import ExerciseProcessor


@pytest.fixture
def sample_exercise_data():
    """Fixture pour créer des données d'exercice de test"""
    return [
        {
            "name": "Push-Up",
            "id": "push_up_1",
            "level": "beginner",
            "equipment": "body only",
            "category": "strength",
            "primaryMuscles": ["chest", "triceps"],
            "secondaryMuscles": ["shoulders"],
            "instructions": ["Step 1", "Step 2", "Step 3"],
            "images": ["img1.jpg", "img2.jpg"],
            "force": "push",
            "mechanic": "compound"
        },
        {
            "name": "Barbell Curl",
            "id": "barbell_curl_1",
            "level": "intermediate",
            "equipment": "barbell",
            "category": "strength",
            "primaryMuscles": ["biceps"],
            "secondaryMuscles": ["forearms"],
            "instructions": ["Step 1", "Step 2"],
            "images": ["img1.jpg"],
            "force": "pull",
            "mechanic": "isolation"
        }
    ]


@pytest.fixture
def processor():
    """Fixture pour créer une instance du processeur"""
    return ExerciseProcessor()


def test_processor_initialization(processor):
    """Test l'initialisation du processeur"""
    assert processor is not None
    assert processor.stats['total_exercises'] == 0
    assert processor.stats['valid_exercises'] == 0


def test_validate_data_with_valid_data(processor, sample_exercise_data):
    """Test la validation avec des données valides"""
    df = pd.DataFrame(sample_exercise_data)
    validated = processor.validate_data(df)
    
    assert len(validated) == 2
    assert processor.stats['valid_exercises'] == 2
    assert processor.stats['invalid_exercises'] == 0


def test_validate_data_rejects_invalid_level(processor):
    """Test que les niveaux invalides sont corrigés"""
    data = [{
        "name": "Test Exercise",
        "id": "test_1",
        "level": "super_expert",  # Invalide
        "equipment": "barbell",
        "category": "strength",
        "primaryMuscles": ["chest"]
    }]
    
    df = pd.DataFrame(data)
    validated = processor.validate_data(df)
    
    # Le niveau invalide doit être remplacé par 'intermediate'
    assert validated.iloc[0]['level'] == 'intermediate'


def test_clean_text_fields(processor, sample_exercise_data):
    """Test le nettoyage des champs textuels"""
    df = pd.DataFrame(sample_exercise_data)
    cleaned = processor.clean_text_fields(df)
    
    # Vérifier que les noms sont en minuscules
    assert cleaned.iloc[0]['name'] == 'push-up'
    assert cleaned.iloc[1]['name'] == 'barbell curl'
    
    # Vérifier que les équipements sont normalisés
    assert cleaned.iloc[0]['equipment'] == 'body only'
    assert cleaned.iloc[1]['equipment'] == 'barbell'


def test_normalize_muscle_groups(processor, sample_exercise_data):
    """Test la normalisation des groupes musculaires"""
    df = pd.DataFrame(sample_exercise_data)
    normalized = processor.normalize_muscle_groups(df)
    
    # Vérifier que all_muscles combine primaires et secondaires
    assert 'all_muscles' in normalized.columns
    assert set(normalized.iloc[0]['all_muscles']) == {'chest', 'triceps', 'shoulders'}
    
    # Vérifier le comptage des muscles
    assert 'muscle_count' in normalized.columns
    assert normalized.iloc[0]['muscle_count'] == 3
    assert normalized.iloc[1]['muscle_count'] == 2


def test_enrich_data(processor, sample_exercise_data):
    """Test l'enrichissement des données"""
    df = pd.DataFrame(sample_exercise_data)
    enriched = processor.enrich_data(df)
    
    # Vérifier les nouveaux champs
    assert 'difficulty_score' in enriched.columns
    assert 'complexity_score' in enriched.columns
    assert 'requires_equipment' in enriched.columns
    assert 'movement_type' in enriched.columns
    
    # Vérifier les valeurs
    assert enriched.iloc[0]['difficulty_score'] == 1  # beginner
    assert enriched.iloc[1]['difficulty_score'] == 2  # intermediate
    
    assert enriched.iloc[0]['requires_equipment'] == False
    assert enriched.iloc[1]['requires_equipment'] == True


def test_remove_duplicates(processor):
    """Test la suppression des doublons"""
    data = [
        {"name": "Push-Up", "id": "push_up_1", "category": "strength", "equipment": "body only", "primaryMuscles": ["chest"]},
        {"name": "Push-Up", "id": "push_up_2", "category": "strength", "equipment": "body only", "primaryMuscles": ["chest"]},  # Doublon par nom
        {"name": "Different", "id": "push_up_1", "category": "strength", "equipment": "body only", "primaryMuscles": ["chest"]},  # Doublon par ID
    ]
    
    df = pd.DataFrame(data)
    deduplicated = processor.remove_duplicates(df)
    
    # Doit garder seulement le premier
    assert len(deduplicated) == 1
    assert processor.stats['duplicates_removed'] == 2


def test_exercise_type_classification(processor, sample_exercise_data):
    """Test la classification compound vs isolation"""
    df = pd.DataFrame(sample_exercise_data)
    normalized = processor.normalize_muscle_groups(df)
    
    # Push-up cible 3 muscles -> compound
    assert normalized.iloc[0]['exercise_type'] == 'compound'
    
    # Barbell curl cible 2 muscles -> isolation
    assert normalized.iloc[1]['exercise_type'] == 'isolation'


def test_movement_type_detection(processor):
    """Test la détection du type de mouvement"""
    data = [
        {"name": "Bench Press", "id": "1", "level": "intermediate", "category": "strength", "equipment": "barbell", "primaryMuscles": ["chest"], "instructions": ["Step 1"]},
        {"name": "Pull-Up", "id": "2", "level": "intermediate", "category": "strength", "equipment": "body only", "primaryMuscles": ["lats"], "instructions": ["Step 1"]},
        {"name": "Running", "id": "3", "level": "beginner", "category": "cardio", "equipment": "body only", "primaryMuscles": ["legs"], "instructions": ["Step 1"]},
    ]
    
    df = pd.DataFrame(data)
    df = processor.clean_text_fields(df)
    enriched = processor.enrich_data(df)
    
    assert enriched.iloc[0]['movement_type'] == 'push'
    assert enriched.iloc[1]['movement_type'] == 'pull'
    assert enriched.iloc[2]['movement_type'] == 'cardio'


def test_complexity_score_calculation(processor):
    """Test le calcul du score de complexité"""
    data = [
        {
            "name": "Simple Exercise",
            "id": "1",
            "level": "beginner",
            "category": "strength",
            "equipment": "body only",
            "primaryMuscles": ["chest"],
            "instructions": ["Step 1", "Step 2"]  # 2 instructions
        }
    ]
    
    df = pd.DataFrame(data)
    df['secondaryMuscles'] = [[]]
    enriched = processor.enrich_data(df)
    
    # difficulty_score = 1 (beginner) + instruction_count / 10 = 1 + 2/10 = 1.2
    assert enriched.iloc[0]['complexity_score'] == 1.2


def test_stats_tracking(processor, sample_exercise_data):
    """Test que les statistiques sont correctement trackées"""
    df = pd.DataFrame(sample_exercise_data)
    
    processor.stats['total_exercises'] = len(df)
    processor.validate_data(df)
    processor.clean_text_fields(df)
    processor.remove_duplicates(df)
    
    stats = processor.get_processing_stats()
    
    assert stats['total_exercises'] == 2
    assert stats['valid_exercises'] == 2
    assert stats['fields_cleaned'] > 0


def test_metadata_columns(processor, sample_exercise_data):
    """Test l'ajout des colonnes de métadonnées"""
    df = pd.DataFrame(sample_exercise_data)
    metadata = {
        'source': 'ExerciseDB',
        'scraped_at': '2026-01-15 10:00:00'
    }
    
    df_with_meta = processor.add_metadata_columns(df, metadata)
    
    assert 'data_source' in df_with_meta.columns
    assert 'scraped_at' in df_with_meta.columns
    assert 'processed_at' in df_with_meta.columns
    
    assert df_with_meta.iloc[0]['data_source'] == 'ExerciseDB'

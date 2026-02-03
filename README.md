# ETL Pipeline - HealthAI Coach

Pipeline ETL pour la collecte, le nettoyage et le chargement des données nutritionnelles, d'exercices et de profils utilisateurs pour le projet HealthAI Coach.

## 📋 Description

Ce projet implémente un pipeline ETL complet pour :
- **Extract** : Scraping de données depuis diverses sources (Kaggle, GitHub, APIs)
- **Transform** : Nettoyage, validation et enrichissement des données avec Pandas
- **Load** : Chargement dans une base de données PostgreSQL

## 🏗️ Architecture

```
ETL/
├── config/              # Fichiers de configuration
│   ├── settings.py      # Configuration globale
│   └── database.py      # Configuration BDD PostgreSQL
├── data/            
│   ├── raw/             # Données brutes récupérées
│   ├── processed/       # Données nettoyées et enrichies
│   └── logs/            # Logs des exécutions
├── src/
│   ├── scrapers/        # Modules de scraping
│   │   ├── exercisedb_scraper.py
│   │   ├── kaggle_scraper.py
│   │   └── run_scraping.py
│   ├── processors/      # Modules de traitement (architecture modulaire par source)
│   │   ├── base_processor.py      # Classe abstraite commune
│   │   ├── run_processing.py      # Orchestrateur
│   │   ├── exercises/             # Logique spécifique aux exercices
│   │   │   ├── processor.py       # ExerciseProcessor
│   │   │   ├── validators.py      # Validation exercices
│   │   │   ├── cleaners.py        # Nettoyage exercices
│   │   │   └── enrichers.py       # Enrichissement exercices
│   │   ├── gym_members/           # Logique spécifique aux membres
│   │   │   ├── processor.py       # GymMembersProcessor
│   │   │   ├── validators.py      # Validation membres
│   │   │   ├── cleaners.py        # Nettoyage membres
│   │   │   └── enrichers.py       # Enrichissement membres
│   │   └── nutrition/             # Logique spécifique à la nutrition
│   │       ├── processor.py       # NutritionProcessor (à venir)
│   │       ├── validators.py      # Validation nutrition
│   │       ├── cleaners.py        # Nettoyage nutrition
│   │       └── enrichers.py       # Enrichissement nutrition
│   └── utils/           # Fonctions utilitaires
│       ├── logger.py    # Système de logging
│       └── file_handler.py # Gestion fichiers JSON/CSV
└── tests/               # Tests unitaires
```

## 🏛️ Architecture Modulaire des Processors

Les processors utilisent une **architecture modulaire par source de données** pour une meilleure maintenabilité :

### Structure par Source de Données

Chaque source de données (exercises, gym_members, nutrition) possède son propre module avec :

**BaseProcessor** (`base_processor.py`)
- Classe abstraite définissant le contrat pour tous les processors
- Gestion centralisée des statistiques et métadonnées
- Pipeline standardisé (validate → clean → enrich → deduplicate)
- Export unifié JSON/CSV

**Module Exercises** (`processors/exercises/`)
- `ExerciseProcessor` : Orchestration du traitement
- `ExerciseValidator` : Règles spécifiques (niveaux, catégories)
- `ExerciseCleaner` : Nettoyage et déduplication
- `ExerciseEnricher` : Enrichissement (muscle groups, difficulty scores, movement types)

**Module Gym Members** (`processors/gym_members/`)
- `GymMembersProcessor` : Orchestration du traitement
- `GymMemberValidator` : Règles spécifiques (âge, poids, BMI, BPM)
- `GymMemberCleaner` : Nettoyage et normalisation (genre, expérience)
- `GymMemberEnricher` : Enrichissement (BMI category, fitness score, age groups)

**Module Nutrition** (`processors/nutrition/`)
- `NutritionProcessor` : Orchestration du traitement (préparé)
- `NutritionValidator` : Règles de validation nutrition
- `NutritionCleaner` : Nettoyage des données nutritionnelles
- `NutritionEnricher` : Enrichissement nutrition (macronutriments, densité calorique)

### Processors Implémentés

- **ExerciseProcessor** : Traitement des exercices ExerciseDB (800+ exercices)
- **GymMembersProcessor** : Traitement des profils membres Kaggle (900+ profils)
- **NutritionProcessor** : Structure prête pour les données nutritionnelles

**Avantages** :
- ✅ Séparation claire des responsabilités par source de données
- ✅ Logique isolée et facilement testable
- ✅ Ajout facile de nouvelles sources (fitness tracker, biométrie)
- ✅ Maintenance simplifiée avec modules indépendants

## 🚀 Installation

### Prérequis
- Python 3.9+
- PostgreSQL 14+
- Git

### Configuration de l'environnement

1. **Cloner le repository**
```bash
git clone <your-repo-url>
cd ETL
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
```

3. **Activer l'environnement virtuel**
```bash
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

4. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

5. **Configurer les variables d'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

## 📊 Sources de données

- **Nutrition** : [Daily Food & Nutrition Dataset](https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset)
- **Recommandations diététiques** : [Diet Recommendations Dataset](https://www.kaggle.com/datasets/ziya07/diet-recommendations-dataset)
- **Exercices** : [ExerciseDB API](https://github.com/ExerciseDB/exercisedb-api)
- **Profils utilisateurs** : [Gym Members Dataset](https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset)
- **Fitness Tracker** : [Fitness Tracker Dataset](https://www.kaggle.com/datasets/nadeemajeedch/fitness-tracker-dataset)

## 🔧 Utilisation

### Exécuter le pipeline complet
```bash
python -m src.processors.run_processing
```

### Exécuter des étapes individuelles
```bash
# Scraping uniquement
python -m src.scrapers.run_scraping

# Traitement ExerciseDB uniquement
python -m src.processors.exercises.processor

# Traitement Gym Members uniquement
python -m src.processors.gym_members.processor

# Chargement BDD (à venir)
python -m src.loaders.run_loading
```

## 🧪 Tests

```bash
# Exécuter tous les tests
pytest

# Avec couverture de code
pytest --cov=src tests/

# Tester un module spécifique
pytest tests/test_exercise_processor.py -v

# Tester les validators
pytest tests/test_validators.py -v
```

### Tests Manuels

```bash
# Tester le nouveau processor ExerciseDB
python -m src.processors.exercises.processor

# Tester le nouveau processor Gym Members
python -m src.processors.gym_members.processor

# Vérifier les fichiers générés
ls data/processed/
```

## 📝 Documentation

- [Cahier des charges](context.md) - Contexte et exigences du projet
- [Guide Scraping](SCRAPING_GUIDE.md) - Comment récupérer les données
- [Guide Processing](PROCESSING_GUIDE.md) - Comment traiter et nettoyer les données
- [Benchmark](benchmark.md) - Performances et métriques
- [Guide de contribution](CONTRIBUTING.md) *(à créer)*
- [Documentation API](docs/API.md) *(à créer)*

## 👥 Équipe

Projet MSPR - EPSI Bloc E6.1
- [Nom Membre 1]
- [Nom Membre 2]
- [Nom Membre 3]
- [Nom Membre 4]

## 📄 Licence

Ce projet est réalisé dans un cadre pédagogique - EPSI 2026

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
│   ├── processors/      # Modules de traitement (architecture modulaire)
│   │   ├── base_processor.py      # Classe abstraite commune
│   │   ├── validators.py          # Logique de validation
│   │   ├── cleaners.py            # Logique de nettoyage
│   │   ├── enrichers.py           # Logique d'enrichissement
│   │   ├── exercise_processor.py  # Processor exercices
│   │   ├── gym_members_processor.py # Processor membres gym
│   │   └── run_processing.py      # Orchestrateur
│   ├── loaders/         # Modules de chargement BDD
│   └── utils/           # Fonctions utilitaires
│       ├── logger.py    # Système de logging
│       └── file_handler.py # Gestion fichiers JSON/CSV
└── tests/               # Tests unitaires
```

## 🏛️ Architecture Modulaire des Processors

Les processors utilisent une **architecture en couches** pour une meilleure maintenabilité :

### Components Réutilisables

**BaseProcessor** (`base_processor.py`)
- Classe abstraite définissant le contrat pour tous les processors
- Gestion centralisée des statistiques et métadonnées
- Pipeline standardisé (validate → clean → enrich → deduplicate)
- Export unifié JSON/CSV

**Validators** (`validators.py`)
- `DataValidator` : Validations génériques (champs requis, plages numériques, catégories)
- `ExerciseValidator` : Règles spécifiques exercices (niveaux, catégories)
- `GymMemberValidator` : Règles spécifiques membres (âge, poids, BMI, BPM)

**Cleaners** (`cleaners.py`)
- `DataCleaner` : Nettoyage générique (texte, duplicates, normalisation)
- `ExerciseCleaner` : Nettoyage spécifique exercices
- `GymMemberCleaner` : Nettoyage spécifique membres (genre, expérience)

**Enrichers** (`enrichers.py`)
- `ExerciseEnricher` : Enrichissement exercices (muscle groups, difficulty scores, movement types)
- `GymMemberEnricher` : Enrichissement membres (BMI category, fitness score, age groups)

### Processors Implémentés

- **ExerciseProcessor** : Traitement des exercices ExerciseDB (800+ exercices)
- **GymMembersProcessor** : Traitement des profils membres Kaggle (900+ profils)

**Avantages** :
- ✅ Code réduit de 60% dans les processors
- ✅ Logique réutilisable entre datasets
- ✅ Tests unitaires simplifiés
- ✅ Ajout facile de nouveaux processors (nutrition, fitness tracker)

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
python -m src.processors.exercise_processor

# Traitement Gym Members uniquement
python -m src.processors.gym_members_processor

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
python -m src.processors.exercise_processor

# Tester le nouveau processor Gym Members
python -m src.processors.gym_members_processor

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

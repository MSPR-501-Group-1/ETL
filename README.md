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
├── config/           # Fichiers de configuration
├── data/            
│   ├── raw/         # Données brutes récupérées
│   ├── processed/   # Données nettoyées
│   └── logs/        # Logs des exécutions
├── src/
│   ├── scrapers/    # Modules de scraping
│   ├── processors/  # Modules de traitement/nettoyage
│   ├── loaders/     # Modules de chargement BDD
│   └── utils/       # Fonctions utilitaires
└── tests/           # Tests unitaires
```

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
python src/main.py
```

### Exécuter des étapes individuelles
```bash
# Scraping uniquement
python src/scrapers/run_scraping.py

# Traitement uniquement
python src/processors/run_processing.py

# Chargement uniquement
python src/loaders/run_loading.py
```

## 🧪 Tests

```bash
# Exécuter tous les tests
pytest

# Avec couverture de code
pytest --cov=src tests/
```

## 📝 Documentation

- [Cahier des charges](context.md)
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

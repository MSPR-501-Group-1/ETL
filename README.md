# HealthAI Coach - ETL

Projet ETL pour la plateforme HealthAI Coach (MSPR EPSI)

## Structure du projet

```
ETL/
├── etl/                    # Code du pipeline ETL
│   ├── extractors/        # Extraction des données
│   ├── transformers/      # Transformation et nettoyage
│   └── loaders/           # Chargement en base de données
├── database/              # Scripts SQL
├── data/
│   ├── raw/              # Données brutes
│   └── processed/        # Données nettoyées
├── logs/                  # Logs d'exécution
├── requirements.txt       # Dépendances Python
└── .env.example          # Variables d'environnement
```

## Installation

1. Créer un environnement virtuel :
```bash
python -m venv venv
```

2. Activer l'environnement :
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

## Utilisation

À compléter...

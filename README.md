# HealthAI ETL

Pipeline ETL PySpark avec exécution en 2 étapes:

1. Transform: extraction + transformation + génération CSV
2. Load: chargement CSV transformé vers PostgreSQL

Le projet expose aussi une API HTTP pour piloter ces étapes.

## Stack

- Python + PySpark
- FastAPI + Uvicorn
- PostgreSQL
- Docker Compose

## Pipelines disponibles

- exercises
- nutrition

## Fonctionnement

Chaque pipeline produit un CSV transformé dans data/processed.

- exercises -> data/processed/exercises/exercise.csv
- nutrition -> data/processed/nutrition/ingredients.csv

Le chargement en base est volontairement séparé pour garder un flux simple et contrôlable.

## Lancer avec Docker

Prérequis:

- Docker
- Docker Compose
- Variables Kaggle si nécessaire pour les datasets Kaggle

Commandes:

```bash
# Build
docker compose build

# Démarrer l'API
docker compose up -d api postgres

# Exécuter un pipeline en CLI (transform)
docker compose run --rm etl-exercises
docker compose run --rm etl-nutrition

# Voir les logs API
docker compose logs -f api
```

## API

Base URL:

- http://localhost:8000

Endpoints:

- POST /api/pipelines/exercises/transform
- POST /api/pipelines/nutrition/transform
- POST /api/pipelines/exercises/load
- POST /api/pipelines/nutrition/load

Réponse standard:

```json
{
  "pipeline": "exercises",
  "status": "transformed"
}
```

ou

```json
{
  "pipeline": "nutrition",
  "status": "loaded"
}
```

## CLI

Entrypoint:

- main.py

Exemple:

```bash
python main.py exercises
python main.py nutrition
```

## Structure utile

```text
api/                    # routes + controllers FastAPI
processors/             # logique extract/transform par pipeline
services/               # orchestration transform/load
utils/                  # load DB, config DB, logs, helpers
spark/                  # gestion session Spark
database/01_initdb.sql  # schéma PostgreSQL
docker-compose.yml      # services postgres, api, etl-*
Dockerfile              # image d'exécution
```

## Notes

- Le schéma SQL est initialisé côté PostgreSQL via database/01_initdb.sql.
- L'environnement local peut afficher des erreurs d'import si les dépendances Python ne sont pas installées hors Docker.
- Le mode recommandé est Docker pour garantir Java/Spark et dépendances alignées.


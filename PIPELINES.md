# HealthAI Coach ETL - Résumé des Pipelines

## 📊 Sources de données implémentées

### 1. Exercises (GitHub)
- **Source** : free-exercise-db
- **URL** : https://github.com/yuhonas/free-exercise-db
- **Type** : JSON
- **Processeur** : `processors/exercises/`
- **Table** : `exercise`
- **Commande** : 
  ```bash
  docker-compose run --rm etl python main.py --pipeline exercises
  ```

### 2. Nutrition - Daily Food (Kaggle)
- **Source** : Daily Food and Nutrition Dataset
- **URL** : https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset
- **Type** : CSV
- **Processeur** : `processors/nutrition/`
- **Table** : `food` (mode: overwrite)
- **Commande** : 
  ```bash
  docker-compose run --rm etl python main.py --pipeline nutrition
  ```

### 3. Nutrition Values - Common Foods (Kaggle)
- **Source** : Nutritional Values for Common Foods and Products
- **URL** : https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products
- **Type** : CSV (dans ZIP)
- **Processeur** : `processors/nutrition_values/`
- **Table** : `food` (mode: append)
- **Commande** : 
  ```bash
  docker-compose run --rm etl python main.py --pipeline nutrition-values
  ```

## 🚀 Commandes de lancement

### Pipeline individuel

```bash
# Exercises
docker-compose run --rm etl python main.py --pipeline exercises

# Nutrition Daily Food
docker-compose run --rm etl python main.py --pipeline nutrition

# Nutrition Values
docker-compose run --rm etl python main.py --pipeline nutrition-values
```

### Pipelines groupés

```bash
# Les deux sources nutrition (Daily Food + Common Foods)
docker-compose run --rm etl python main.py --pipeline nutrition-all

# Tous les pipelines (Exercises + Nutrition)
docker-compose run --rm etl python main.py --pipeline all
```

## 📂 Sorties des données

### Parquet
```
data/processed/
├── exercises.parquet          # Exercises pipeline
├── nutrition.parquet          # Nutrition Daily Food pipeline
└── nutrition_values.parquet   # Nutrition Values pipeline
```

### CSV
```
data/processed/
├── exercises_csv/             # Exercises pipeline
├── nutrition_csv/             # Nutrition Daily Food pipeline
└── nutrition_values_csv/      # Nutrition Values pipeline
```

### PostgreSQL
```
healthai_db
├── exercise            # Exercises (873 rows)
├── food                # Nutrition (multiple sources, append mode)
├── data_source         # Metadata - 3 sources
├── etl_execution       # Execution logs
└── data_quality_check  # Quality checks
```

## ⚠️ Notes importantes

### Mode d'écriture PostgreSQL

- **nutrition** : Mode `OVERWRITE` - Remplace toutes les données de la table `food`
- **nutrition-values** : Mode `APPEND` - Ajoute à la table `food` existante

**Recommandation** : Toujours lancer `nutrition` avant `nutrition-values` pour avoir les deux sources :

```bash
docker-compose run --rm etl python main.py --pipeline nutrition-all
```

### Prérequis Kaggle

Les deux pipelines nutrition nécessitent les credentials Kaggle :

```powershell
# Configuration
mkdir $HOME\.kaggle -Force
copy kaggle.json $HOME\.kaggle\kaggle.json

# Vérification
python scripts/verify_nutrition.py
```

## 🧪 Tests par étape

### Extract
```bash
docker-compose run --rm etl python -m processors.nutrition.extract
docker-compose run --rm etl python -m processors.nutrition_values.extract
```

### Transform
```bash
docker-compose run --rm etl python -m processors.nutrition.transform
docker-compose run --rm etl python -m processors.nutrition_values.transform
```

### Load
```bash
docker-compose run --rm etl python -m processors.nutrition.load
docker-compose run --rm etl python -m processors.nutrition_values.load
```

## 📊 Vérification des résultats

```bash
# Connexion PostgreSQL
docker exec -it healthai_postgres psql -U healthai -d healthai_db

# Comptage
SELECT COUNT(*) FROM exercise;
SELECT COUNT(*) FROM food;

# Détails par source (si métadonnées disponibles)
SELECT source_name, records_loaded, status 
FROM etl_execution e
JOIN data_source s ON e.source_id = s.source_id
ORDER BY e.started_at DESC;

# Aperçu données
SELECT name, calories_100g, protein_100g, category_ref FROM food LIMIT 10;
```

## 🏗️ Architecture MCD

### Table EXERCISE
- exercise_id (UUID, PK)
- name, body_part_target, video_url, description
- difficulty_level, equipment_required, category
- created_at, updated_at

### Table FOOD
- food_id (UUID, PK)
- name, brand
- calories_100g, protein_100g, carbs_100g, fat_100g
- nutriscore, category_ref
- fiber_g, sugar_g, sodium_mg, cholesterol_mg
- created_at, updated_at

## 📈 Progression du projet

✅ **Sources implémentées : 3/3 minimum requis**
- ✅ Exercises (GitHub)
- ✅ Nutrition Daily Food (Kaggle)
- ✅ Nutrition Values (Kaggle)

🎯 **Objectif MSPR atteint** : Minimum 2 sources de données

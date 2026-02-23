# Guide de démarrage rapide - MSPR HealthAI Coach ETL

## ⚠️ RÈGLE #1 : TOUJOURS utiliser Docker

**POURQUOI ?**
- PySpark 3.5.0 nécessite Java 17 (incompatible avec Java 25+)
- Docker embarque Java 17 LTS automatiquement
- Les tests locaux peuvent échouer avec des versions Java récentes

## 🚀 Commandes essentielles

### 1️⃣ Premier lancement (pipeline exercises)

```powershell
# Construction et lancement complet
docker-compose up --build

# Vérifier les résultats
.\scripts\verify.ps1
```

### 2️⃣ Pipelines nutrition (nécessite Kaggle)

**Prérequis Kaggle :**
```powershell
# Télécharger kaggle.json depuis https://www.kaggle.com/account
mkdir $HOME\.kaggle -Force
copy kaggle.json $HOME\.kaggle\kaggle.json

# Vérifier la configuration
python scripts/verify_nutrition.py
```

**Lancer les pipelines nutrition :**
```powershell
# Daily Food dataset
docker-compose run --rm etl python main.py --pipeline nutrition

# Common Foods dataset
docker-compose run --rm etl python main.py --pipeline nutrition-values

# Les deux sources nutrition ensemble (RECOMMANDÉ)
docker-compose run --rm etl python main.py --pipeline nutrition-all
```

### 3️⃣ Tous les pipelines

```powershell
docker-compose run --rm etl python main.py --pipeline all
```

### 4️⃣ Pipelines spécifiques

```powershell
# Exercises seulement
docker-compose run --rm etl python main.py --pipeline exercises

# Nutrition Daily Food seulement
docker-compose run --rm etl python main.py --pipeline nutrition

# Nutrition Values seulement
docker-compose run --rm etl python main.py --pipeline nutrition-values

# Les deux nutrition ensemble
docker-co (Daily Food)
docker-compose run --rm etl python -m processors.nutrition.extract

# Extract (Common Foods)
docker-compose run --rm etl python -m processors.nutrition_values.extract

# Transform (Daily Food)
docker-compose run --rm etl python -m processors.nutrition.transform

# Transform (Common Foods)
docker-compose run --rm etl python -m processors.nutrition_values.transform

# Load (Daily Food)
docker-compose run --rm etl python -m processors.nutrition.load

# Load (Common Foods)
docker-compose run --rm etl python -m processors.nutrition_values.extract

# Transform
docker-compose run --rm etl python -m processors.nutrition.transform

# Load
docker-compose run --rm etl python -m processors.nutrition.load
```

## 🗄️ Accéder à la base de données

```powershell
# Se connecter à PostgreSQL
docker exec -it healthai_postgres psql -U healthai -d healthai_db

# Requêtes utiles
SELECT COUNT(*) FROM exercise;
SELECT COUNT(*) FROM food;

SELECT name, difficulty_level FROM exercise LIMIT 5;
SELECT name, calories_100g, protein_100g FROM food LIMIT 5;

\q  # Quitter
```

## 🛑 Arrêter les services

```powershell
# Arrêt simple
docker-compose down

# Supprimer les données (reset complet)
docker-compose down -v
```

## 🔍 Vérifications

```powershell
# Vérifier la configuration nutrition
python scripts/verify_nutrition.py

# Vérifier les résultats exercises
.\scripts\verify.ps1
```

## 📊 Sorties des pipelines

Après exécution, les données sont disponibles dans :

```
data/
├── raw/                      # Données brutes téléchargées
│   ├── exercises.json       # GitHub API
│   └── nutrition_*.csv      # Kaggle dataset
└── processed/             nutrition + nutrition_values combinés)
- Tables metadata : `data_source`, `etl_execution`, `data_quality_check`

**Note importante** : 
- Le pipeline `nutrition` **remplace** les données de la table `food`
- Le pipeline `nutrition-values` **ajoute** à la table `food`
- Utiliser `nutrition-all` pour avoir les deux sources ensemble
    ├── exercises_csv/       # CSV pour analyse
    ├── nutrition.parquet    # Format Parquet
    └── nutrition_csv/       # CSV pour analyse
```

**Base PostgreSQL :**
- Table `exercise` : 873 lignes
- Table `food` : Variable (selon dataset Kaggle)
- Tables metadata : `data_source`, `etl_execution`, `data_quality_check`

## ❌ NE PAS FAIRE

- ❌ `python main.py --pipeline nutrition` (sans Docker)
- ❌ `pip install -r requirements.txt` puis exécution locale
- ❌ Installer Java manuellement

**Toujours préférer :**
- ✅ `docker-compose run --rm etl python main.py --pipeline nutrition`

## 🆘 Troubleshooting

**Problème : "Java version not compatible"**
→ Tu exécutes en local, utilise Docker !

**Problème : "Kaggle credentials not found"**
→ Vérifier que `kaggle.json` est dans `$HOME\.kaggle\`

**Problème : "Connection refused postgres"**
→ Lancer d'abord : `docker-compose up -d postgres`

**Problème : "Port 5432 already in use"**
→ Arrêter PostgreSQL local ou changer le port dans docker-compose.yml

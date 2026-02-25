# HealthAI Coach - Pipeline ETL

Pipeline ETL avec PySpark pour le projet HealthAI Coach.

## ⚠️ Docker OBLIGATOIRE

PySpark 3.5.0 nécessite Java 17 (incompatible avec Java 25+). Docker embarque Java 17 LTS automatiquement.

## 🚀 Démarrage rapide

### Prérequis
- Docker & Docker Compose
- [Compte Kaggle](https://www.kaggle.com) + API key pour 5 des 6 pipelines

### Configuration Kaggle

```powershell
# 1. Télécharger kaggle.json depuis https://www.kaggle.com/account
mkdir $HOME\.kaggle -Force
copy kaggle.json $HOME\.kaggle\kaggle.json
```

### Premier lancement

```bash
# Tout construire et lancer (exécute --pipeline all)
docker-compose up --build

# Vérifier
.\scripts\verify.ps1
docker exec -it healthai_postgres psql -U healthai -d healthai_db -c "SELECT COUNT(*) FROM exercise;"
```

## 📊 Sources de données (6/6 implémentées)

| Pipeline | Source | Type | Tables | Lignes |
|----------|--------|------|--------|--------|
| **exercises** | [free-exercise-db](https://github.com/yuhonas/free-exercise-db) | GitHub JSON | `exercise` | 873 |
| **nutrition** | [Daily Food Dataset](https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset) | Kaggle CSV | `food` | ~9000 |
| **nutrition-values** | [Common Foods](https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products) | Kaggle CSV | `food` | append |
| **gym-members** | [Gym Members](https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset) | Kaggle CSV | `user`, `user_profile`, `user_metrics` | 973 |
| **fitness-tracker** | [Fitness Tracker](https://www.kaggle.com/datasets/nadeemajeedch/fitness-tracker-dataset) | Kaggle CSV | `activity_type`, `workout_session` | variable |
| **body-performance** | [Body Performance](https://www.kaggle.com/datasets/kukuroo3/body-performance-data) | Kaggle CSV | `workout_session`, `session_detail` | variable |

## 🎮 Commandes pipelines

```bash
# Pipelines individuels
docker-compose run --rm etl python main.py --pipeline exercises
docker-compose run --rm etl python main.py --pipeline nutrition
docker-compose run --rm etl python main.py --pipeline nutrition-values
docker-compose run --rm etl python main.py --pipeline gym-members
docker-compose run --rm etl python main.py --pipeline fitness-tracker
docker-compose run --rm etl python main.py --pipeline body-performance

# Pipelines groupés
docker-compose run --rm etl python main.py --pipeline nutrition-all  # nutrition + nutrition-values
docker-compose run --rm etl python main.py --pipeline workouts       # fitness-tracker + body-performance
docker-compose run --rm etl python main.py --pipeline all            # Tous les 6 pipelines
```

### ⚠️ Ordre d'exécution recommandé (dépendances FK)

1. `exercises` → requis par body-performance (session_detail)
2. `gym-members` → requis par fitness-tracker et body-performance (user_id)
3. `nutrition-all` → indépendant
4. `workouts` → nécessite exercises + gym-members

**Best practice**: `docker-compose run --rm etl python main.py --pipeline all`

### Modes d'écriture PostgreSQL

- **nutrition**: `OVERWRITE` (remplace `food`)
- Tous les autres: `APPEND`

## 📁 Structure du projet

```
ETL2/
├── processors/          # 6 pipelines ETL (exercises, nutrition x2, gym_members, fitness_tracker, body_performance)
│   └── {pipeline}/     # Chaque pipeline: extract.py, transform.py, load.py, pipeline.py, config.py
├── spark/              # Session PySpark singleton
├── data/
│   ├── raw/           # Données brutes téléchargées
│   └── processed/     # Parquet + CSV outputs
├── database/
│   └── init.sql       # Schéma PostgreSQL (12 tables)
├── scripts/
│   └── verify.ps1     # Vérification résultats
├── main.py            # Orchestrateur principal
├── Dockerfile         # Java 17 + PySpark 3.5.0
└── docker-compose.yml # postgres + etl services
```

## 🗄️ Base de données PostgreSQL

**Connexion**: `localhost:5432` | User: `healthai` | Pass: `password` | DB: `healthai_db`

**12 Tables créées**:
- `exercise` (873 exercices) | `food` (~9000 aliments)
- `user`, `user_profile`, `user_metrics` (973 utilisateurs)
- `activity_type`, `workout_session`, `session_detail` (tracking entraînements)
- `health_goal` (référence 5 objectifs)
- `data_source`, `etl_execution`, `data_quality_check` (métadonnées ETL)

```sql
-- Requêtes utiles
docker exec -it healthai_postgres psql -U healthai -d healthai_db

SELECT COUNT(*) FROM exercise;
SELECT COUNT(*) FROM food;
SELECT COUNT(*) FROM "user";
SELECT name, difficulty_level FROM exercise LIMIT 5;
```

## 📦 Sorties des données

1. **PostgreSQL** → 12 tables relationnelles (requêtables SQL)
2. **Parquet** → `data/processed/*.parquet` (analytics, optimisé)  
3. **CSV** → `data/processed/*_csv/` (Excel compatible)

## 🐛 Troubleshooting

```bash
# Logs
docker logs healthai_etl
docker-compose logs -f

# Reset complet
docker-compose down -v
docker-compose up --build

# Port 5432 occupé
netstat -ano | findstr :5432
taskkill /PID <PID> /F
```

## 🛠️ Développement local (⚠️ NON RECOMMANDÉ)

**ATTENTION**: Nécessite Java 17. Privilégier Docker.

```powershell
# 1. Vérifier Java
java -version  # Si >= 25, utiliser Docker obligatoirement

# 2. Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. PostgreSQL local
docker run -d --name postgres_local `
  -e POSTGRES_USER=healthai -e POSTGRES_PASSWORD=password `
  -e POSTGRES_DB=healthai_db -p 5432:5432 postgres:15-alpine
docker exec -i postgres_local psql -U healthai -d healthai_db < database/init.sql

# 4. Exécuter
python main.py --pipeline exercises
```

## 📈 Architecture technique

- **Stack**: PySpark 3.5.0 + PostgreSQL 15 + Docker
- **Pattern ETL**: Extract (GitHub/Kaggle) → Transform (PySpark DataFrame) → Load (JDBC + Parquet + CSV)
- **Dépendances**: Java 17, Python 3.x, pandas, psycopg2-binary, kaggle CLI
- **Schéma MCD**: 12 tables relationnelles avec contraintes FK/PK (UUID)


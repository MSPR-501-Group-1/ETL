# HealthAI Coach - Pipeline ETL

Pipeline ETL avec PySpark pour le projet HealthAI Coach.

## ⚠️ IMPORTANT : Utiliser Docker

**Docker est OBLIGATOIRE** pour éviter les problèmes de compatibilité Java :
- PySpark 3.5.0 nécessite Java 17 (incompatible avec Java 25+)
- Docker embarque Java 17 LTS (eclipse-temurin:17-jdk)
- L'exécution locale peut échouer si Java 25+ est installé

## 🚀 Démarrage rapide avec Docker

### Prérequis
- Docker & Docker Compose installés
- 4GB de RAM disponible
- **Pour le pipeline nutrition** : [Clé API Kaggle](https://www.kaggle.com/account) (voir section Configuration Kaggle)

### Installation & Lancement

```bash
# 1. Copier les variables d'environnement
cp .env.example .env

# 2. Construire et lancer les services (exécute le pipeline ETL complet)
docker-compose up --build

# Cela va :
# - Démarrer PostgreSQL
# - Exécuter l'ETL : Extract → Transform → Load
# - Sauvegarder les données dans PostgreSQL + Parquet + CSV
```

### Vérifier les résultats

```bash
# Connexion à PostgreSQL
docker exec -it healthai_postgres psql -U healthai -d healthai_db

# Requêtes SQL
SELECT COUNT(*) FROM exercise;
SELECT name, difficulty_level, equipment_required FROM exercise LIMIT 5;
\q  # Quitter
```

**Ou via script PowerShell** :

```powershell
.\scripts\verify.ps1
```

### Exécuter des pipelines spécifiques

```bash
# Tous les pipelines
docker-compose run --rm etl python3 main.py --pipeline all

# Pipeline exercises uniquement
docker-compose run --rm etl python3 main.py --pipeline exercises

# Pipeline nutrition uniquement
docker-compose run --rm etl python3 main.py --pipeline nutrition

# Étapes individuelles
docker-compose run --rm etl python3 -m processors.exercises.extract
docker-compose run --rm etl python3 -m processors.exercises.transform
docker-compose run --rm etl python3 -m processors.exercises.load
```

### Arrêter les services

```bash
# Arrêt simple
docker-compose down

# Supprimer les volumes (efface la base de données)
docker-compose down -v
```

## 📁 Structure du projet

```
ETL2/
├── processors/          # Pipelines ETL par source
│   ├── exercises/      # Pipeline données exercices (GitHub)
│   │   ├── extract.py  # Téléchargement données brutes
│   │   ├── transform.py # Transformation PySpark → MCD
│   │   ├── load.py     # Chargement PostgreSQL
│   │   ├── pipeline.py # Orchestrateur complet
│   │   └── config.py   # Configuration
│   └── nutrition/      # Pipeline données nutrition (Kaggle)
│       ├── extract.py  # Téléchargement via Kaggle CLI
│       ├── transform.py # Transformation PySpark → MCD
│       ├── load.py     # Chargement PostgreSQL
│       ├── pipeline.py # Orchestrateur complet
│       └── config.py   # Configuration
├── spark/              # Gestionnaire session Spark
│   └── session.py      # Session singleton
├── data/               # Répertoires données
│   ├── raw/           # Données brutes
│   └── processed/     # Données transformées
├── database/           # Schémas SQL
│   └── init.sql       # Initialisation tables
├── scripts/           # Scripts utilitaires
│   └── verify.ps1     # Vérification résultats
├── main.py            # Point d'entrée principal
├── Dockerfile         # Image Docker
└── docker-compose.yml # Orchestration services
```

## 🛠️ Développement local (⚠️ NON RECOMMANDÉ)

**ATTENTION** : L'exécution locale peut échouer si vous avez Java 25+ installé.
**Privilégier Docker** qui embarque Java 17 compatible.

### Installation (si vraiment nécessaire)

```powershell
# Vérifier la version Java (DOIT être < 25)
java -version  # Si >= 25, utiliser Docker

# 1. Créer l'environnement virtuel
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer PostgreSQL seul
docker run -d --name postgres_local `
  -e POSTGRES_USER=healthai `
  -e POSTGRES_PASSWORD=password `
  -e POSTGRES_DB=healthai_db `
  -p 5432:5432 postgres:15-alpine

# 4. Initialiser la base de données
docker exec -i postgres_local psql -U healthai -d healthai_db < database/init.sql
```

### Exécution des pipelines

```powershell
# Pipeline complet
python main.py --pipeline exercises

# Étapes individuelles
python -m processors.exercises.extract
python -m processors.exercises.transform
python -m processors.exercises.load
```

### Nettoyage

```powershell
docker stop postgres_local
docker rm postgres_local
```

## 📊 Sources de données

### ✅ Implémentées
- **Exercices** : [free-exercise-db](https://github.com/yuhonas/free-exercise-db) - 873 exercices (GitHub)
- **Nutrition Daily Food** : [Daily Food & Nutrition Dataset](https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset) (Kaggle)
- **Nutrition Values** : [Nutritional Values for Common Foods](https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products) (Kaggle)

### 🔧 Configuration Kaggle (pour pipelines nutrition)

1. Créer un compte sur [Kaggle](https://www.kaggle.com)
2. Télécharger `kaggle.json` depuis [Account Settings](https://www.kaggle.com/account)
3. Placer le fichier :
   ```powershell
   # Windows
   mkdir $HOME\.kaggle -Force
   copy kaggle.json $HOME\.kaggle\kaggle.json
   ```
4. Vérifier : `python scripts/verify_nutrition.py`

### ❌ À implémenter
- **Utilisateurs** : Gym Members, Fitness Tracker datasets

### 🚀 Lancer les pipelines

```bash
# Pipeline exercises
docker-compose run --rm etl python main.py --pipeline exercises

# Pipeline nutrition (Daily Food)
docker-compose run --rm etl python main.py --pipeline nutrition

# Pipeline nutrition-values (Common Foods)
docker-compose run --rm etl python main.py --pipeline nutrition-values

# Les deux nutrition ensemble (RECOMMANDÉ)
docker-compose run --rm etl python main.py --pipeline nutrition-all

# Tout ensemble
docker-compose run --rm etl python main.py --pipeline all
```

Voir [PIPELINES.md](PIPELINES.md) pour plus de détails.

## 🗄️ Base de données

PostgreSQL accessible sur `localhost:5432`
- Base : `healthai_db`
- Utilisateur : `healthai`
- Mot de passe : `password`

**Tables créées :**
- `exercise` - Catalogue d'exercices (schéma MCD)
- `food` - Catalogue d'aliments nutritionnels (schéma MCD)
- `etl_execution` - Métadonnées d'exécution ETL
- `data_quality_check` - Contrôles qualité
- `data_source` - Registre des sources (3 sources)

**Connexion** : `psql -h localhost -U healthai -d healthai_db`

## 📦 Données de sortie

Après exécution des pipelines, les données sont disponibles dans :

1. **PostgreSQL** - Tables `exercise` et `food` (interrogeables en SQL)
2. **Parquet** - `data/processed/*.parquet` (optimisé pour analytics)
3. **CSV** - `data/processed/*_csv/` (compatible Excel/analytics)
3. **CSV** - `data/processed/exercises_csv/` (exports lisibles)

## 🔍 Vérification du pipeline

```powershell
# Via script PowerShell
.\scripts\verify.ps1

# Ou manuellement
docker exec healthai_postgres psql -U healthai -d healthai_db -c "SELECT COUNT(*) FROM exercise;"
```

**Résultats attendus** :
- ✅ ~873 exercices dans PostgreSQL
- ✅ Fichier Parquet créé (~500KB)
- ✅ Export CSV généré
- ✅ Logs ETL dans `etl_execution`

## 🐛 Troubleshooting

### Voir les logs

```bash
# Logs conteneur ETL
docker logs healthai_etl

# Logs PostgreSQL
docker logs healthai_postgres

# Logs en temps réel
docker-compose logs -f etl
```

### Redémarrer proprement

```bash
# Supprimer tous les conteneurs et volumes
docker-compose down -v

# Rebuild et relancer
docker-compose up --build
```

### Problèmes courants

**Erreur "port 5432 already in use"** :
```bash
# Trouver et arrêter le processus
netstat -ano | findstr :5432
taskkill /PID <PID> /F
```

**Données corrompues** :
```bash
# Supprimer et re-extraire
rm data/raw/exercises/exercises.json
docker-compose run --rm etl python3 -m processors.exercises.extract
```

## 📈 Prochaines étapes

- [ ] Implémenter pipeline nutrition
- [ ] Implémenter pipeline utilisateurs  
- [ ] Ajouter dashboard de visualisation
- [ ] Implémenter contrôles qualité avancés
- [ ] Ajouter API REST pour consultation
- [ ] Orchestration avec Apache Airflow

## 🤝 Contributeurs

Projet MSPR - EPSI 2026  
Équipe : [Vos noms]

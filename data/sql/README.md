# 🗄️ Scripts SQL - Base de Données HealthAI Coach

## 📁 Structure des fichiers

- `01_create_tables.sql` - Création de toutes les tables
- `02_indexes.sql` - Index pour optimiser les performances  
- `03_constraints.sql` - Contraintes métier et validation
- `04_initial_data.sql` - Données de référence initiales
- `05_views.sql` - Vues pour simplifier l'API
- `setup_database.sql` - Script complet d'installation

## 🚀 Utilisation

### Installation complète PostgreSQL
```bash
psql -U postgres -d healthai_coach -f setup_database.sql
```

### Installation étape par étape
```bash
psql -U postgres -d healthai_coach -f 01_create_tables.sql
psql -U postgres -d healthai_coach -f 02_indexes.sql
psql -U postgres -d healthai_coach -f 03_constraints.sql
psql -U postgres -d healthai_coach -f 04_initial_data.sql
psql -U postgres -d healthai_coach -f 05_views.sql
```

### Test SQLite (développement)
```bash
cd ../../
python -c "from src.loaders.sqlite_loader import SQLiteLoader; SQLiteLoader().create_tables_from_mermaid()"
```

## 📊 Tables principales

- `users`, `user_profiles` - Utilisateurs et profils
- `exercises` - Catalogue d'exercices (depuis ETL)
- `user_metrics` - Métriques utilisateurs (depuis ETL)
- `foods`, `recipes` - Nutrition
- `workout_sessions` - Sessions d'entraînement
- `data_sources`, `etl_executions` - Métadonnées ETL

## 🔧 Migration SQLite → PostgreSQL

Le SQLiteLoader peut être utilisé pour le développement, puis migrer vers PostgreSQL avec ces scripts pour la production.
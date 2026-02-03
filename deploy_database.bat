REM Script de déploiement Windows - Base de données + Données

echo 🏗️ Création de la base de données...
sqlite3 data/database.db ".read data/sql/01_create_tables.sql"
sqlite3 data/database.db ".read data/sql/04_initial_data.sql"

echo 📂 Chargement des données processed...
python src/loaders/data_loader.py load

echo 📊 Statistiques finales...
python src/loaders/data_loader.py stats

echo ✅ Déploiement terminé! Base prête dans data/database.db
pause
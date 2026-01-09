# 📥 Guide de Scraping - ETL Pipeline

## 🎯 Objectif

Ce guide explique comment récupérer les données depuis différentes sources et les sauvegarder en format JSON/CSV.

---

## 📚 Sources de données

### 1. ExerciseDB (GitHub) ✅ Prêt
- **Source** : [Free Exercise DB](https://github.com/yuhonas/free-exercise-db)
- **Format** : JSON via API
- **Authentification** : Aucune
- **Scraper** : `src/scrapers/exercisedb_scraper.py`

### 2. Datasets Kaggle 🔑 Nécessite configuration
- **Sources** :
  - Daily Food & Nutrition Dataset
  - Diet Recommendations Dataset
  - Gym Members Exercise Dataset
  - Fitness Tracker Dataset
- **Format** : CSV (téléchargement puis extraction)
- **Authentification** : API Kaggle requise
- **Scraper** : `src/scrapers/kaggle_scraper.py`

---

## 🚀 Utilisation

### Option 1 : Scraper ExerciseDB (Simple - Aucune config requise)

```bash
# Activer l'environnement virtuel
source venv/Scripts/activate

# Exécuter le scraper ExerciseDB
python -m src.scrapers.exercisedb_scraper
```

**Résultat** : Fichier JSON créé dans `data/raw/exercisedb_raw_YYYYMMDD_HHMMSS.json`

### Option 2 : Télécharger depuis Kaggle (Nécessite configuration)

#### Étape 1 : Configuration Kaggle API

1. **Créer un compte Kaggle** : [kaggle.com](https://www.kaggle.com)

2. **Obtenir votre token API** :
   - Aller sur : https://www.kaggle.com/account
   - Cliquer sur "Create New API Token"
   - Un fichier `kaggle.json` sera téléchargé

3. **Placer le token** :
   ```bash
   # Windows
   mkdir %USERPROFILE%\.kaggle
   move kaggle.json %USERPROFILE%\.kaggle\
   
   # Linux/Mac
   mkdir -p ~/.kaggle
   mv kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

4. **Installer Kaggle CLI** :
   ```bash
   pip install kaggle
   ```

#### Étape 2 : Télécharger les datasets

```bash
# Télécharger un seul dataset
python -m src.scrapers.kaggle_scraper

# Ou télécharger tous les datasets via le pipeline complet
python -m src.scrapers.run_scraping
```

### Option 3 : Pipeline complet

```bash
python -m src.scrapers.run_scraping
```

Cette commande exécute tous les scrapers séquentiellement.

---

## 📂 Structure des données récupérées

### ExerciseDB
```
data/raw/exercisedb_raw_YYYYMMDD_HHMMSS.json
{
  "metadata": {
    "source": "ExerciseDB",
    "total_exercises": 800+,
    "categories": {...},
    "scraped_at": "2026-01-09 14:30:00"
  },
  "exercises": [
    {
      "name": "3/4 Sit-Up",
      "category": "strength",
      "equipment": "body only",
      "primaryMuscles": ["abdominals"],
      "images": ["url1", "url2"],
      ...
    }
  ]
}
```

### Kaggle Datasets
```
data/raw/kaggle/
├── daily-food-and-nutrition-dataset/
│   └── *.csv
├── diet-recommendations-dataset/
│   └── *.csv
├── gym-members-exercise-dataset/
│   └── *.csv
└── fitness-tracker-dataset/
    └── *.csv
```

---

## 🔍 Vérification des données

### Voir les logs

```bash
cat data/logs/etl.log
```

### Lister les fichiers téléchargés

```bash
ls -R data/raw/
```

---

## ⚠️ Résolution de problèmes

### Erreur : Kaggle API not found

```bash
pip install kaggle
```

### Erreur : 401 Unauthorized (Kaggle)

Vérifiez que `kaggle.json` est bien placé dans `~/.kaggle/` et contient vos credentials.

### Erreur : Module not found

```bash
# S'assurer que l'environnement virtuel est activé
source venv/Scripts/activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur : Connection timeout

Augmentez le timeout dans `.env` :
```
TIMEOUT=60
```

---

## 📊 Prochaines étapes

Une fois les données récupérées :
1. ✅ Vérifier l'intégrité des fichiers
2. 🧹 Nettoyer les données avec les processors
3. 💾 Charger dans la base de données PostgreSQL
4. 📈 Créer les visualisations

---

## 🛠️ Personnalisation

### Ajouter une nouvelle source

1. Créer un nouveau scraper dans `src/scrapers/`
2. Hériter de la classe de base ou créer une nouvelle classe
3. Implémenter les méthodes `fetch()` et `save()`
4. Ajouter au pipeline dans `run_scraping.py`

### Exemple de structure :

```python
from src.utils.logger import setup_logger
from src.utils.file_handler import save_to_json

class MyCustomScraper:
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    def fetch_data(self):
        # Votre logique de récupération
        pass
    
    def run(self):
        data = self.fetch_data()
        save_to_json(data, "output.json")
        return data
```

---

**Document créé pour : EPSI MSPR - ETL Pipeline**  
**Dernière mise à jour : 9 janvier 2026**

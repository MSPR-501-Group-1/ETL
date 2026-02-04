# 📊 Guide de Traitement des Données - Module Processing

## 🎯 Objectif

Ce module transforme les données brutes en données exploitables pour l'analyse et le chargement en base de données.

---

## 📁 Structure du Module

```
src/processors/
├── __init__.py
├── base_processor.py          # Classe de base abstraite commune
├── run_processing.py          # Orchestrateur de tous les processeurs
├── exercises/                 # Module exercices ExerciseDB
│   ├── __init__.py
│   ├── processor.py           # ExerciseProcessor
│   ├── validators.py          # Validation exercices
│   ├── cleaners.py            # Nettoyage exercices
│   └── enrichers.py           # Enrichissement exercices
├── gym_members/               # Module membres de gym
│   ├── __init__.py
│   ├── processor.py           # GymMembersProcessor
│   ├── validators.py          # Validation membres
│   ├── cleaners.py            # Nettoyage membres
│   └── enrichers.py           # Enrichissement membres
└── nutrition/                 # Module nutrition (préparé)
    ├── __init__.py
    ├── processor.py           # NutritionProcessor
    ├── validators.py          # Validation nutrition
    ├── cleaners.py            # Nettoyage nutrition
    └── enrichers.py           # Enrichissement nutrition
```

---

## 🔄 Pipeline de Transformation

### ExerciseProcessor - Exercices ExerciseDB

**Étapes du pipeline :**

1. **Chargement** : Lecture du fichier JSON brut
2. **Validation** : Vérification des champs obligatoires et cohérence
3. **Nettoyage** : Normalisation des champs textuels (trim, lowercase)
4. **Normalisation** : Standardisation des groupes musculaires
5. **Enrichissement** : Ajout de colonnes calculées
6. **Déduplication** : Suppression des doublons
7. **Export** : Sauvegarde JSON + CSV

**Transformations appliquées :**

| Transformation | Description | Exemple |
|---------------|-------------|---------|
| **Nettoyage texte** | Normalisation casse et espaces | "Push-Up" → "push-up" |
| **Validation niveau** | Contrôle des valeurs | "advanced" → "intermediate" |
| **Muscles combinés** | Fusion primaires + secondaires | `all_muscles: ["chest", "triceps"]` |
| **Score difficulté** | Conversion numérique | beginner → 1, expert → 3 |
| **Type exercice** | Classification composé/isolation | muscle_count > 2 → "compound" |
| **Score complexité** | Basé sur difficulté + instructions | difficulty_score + (instructions/10) |
| **Équipement requis** | Booléen | "body only" → false, "barbell" → true |
| **Type mouvement** | Push/Pull/Cardio/Stretching | "bench press" → "push" |

**Colonnes enrichies ajoutées :**

- `all_muscles` : Liste combinée muscles primaires + secondaires
- `muscle_count` : Nombre de muscles ciblés
- `exercise_type` : "compound" ou "isolation"
- `difficulty_score` : 1 (beginner), 2 (intermediate), 3 (expert)
- `instruction_count` : Nombre d'étapes dans les instructions
- `complexity_score` : Score calculé (difficulté + complexité instructions)
- `requires_equipment` : Booléen (true si équipement nécessaire)
- `movement_type` : "push", "pull", "cardio", "stretching", "other"
- `data_source` : Source des données ("ExerciseDB")
- `scraped_at` : Date du scraping original
- `processed_at` : Date du traitement

---

## 🚀 Utilisation

### Option 1 : Traiter uniquement ExerciseDB

```bash
# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Exécuter le processor ExerciseDB
python -m src.processors.exercises.processor

# Ou exécuter le processor Gym Members
python -m src.processors.gym_members.processor
```

**Résultat :**
- `data/processed/exercises_processed_YYYYMMDD_HHMMSS.json` (avec métadonnées)
- `data/processed/exercises_processed_YYYYMMDD_HHMMSS.csv` (format tabulaire)

### Option 2 : Orchestrer tous les processeurs

```bash
python -m src.processors.run_processing
```

---

## 📊 Exemple de Données Traitées

### Avant (Raw)
```json
{
  "name": "Barbell Bench Press",
  "level": "intermediate",
  "equipment": "barbell",
  "primaryMuscles": ["chest"],
  "secondaryMuscles": ["triceps", "shoulders"],
  "instructions": ["Step 1...", "Step 2...", "Step 3...", "Step 4..."]
}
```

### Après (Processed)
```json
{
  "name": "barbell bench press",
  "level": "intermediate",
  "equipment": "barbell",
  "primaryMuscles": ["chest"],
  "secondaryMuscles": ["triceps", "shoulders"],
  "all_muscles": ["chest", "triceps", "shoulders"],
  "muscle_count": 3,
  "exercise_type": "compound",
  "difficulty_score": 2,
  "instruction_count": 4,
  "complexity_score": 2.4,
  "requires_equipment": true,
  "movement_type": "push",
  "data_source": "ExerciseDB",
  "scraped_at": "2026-01-09 15:47:18",
  "processed_at": "2026-01-15T21:26:11.602072",
  "instructions": ["Step 1...", "Step 2...", "Step 3...", "Step 4..."]
}
```

---

## 📈 Statistiques de Traitement

Le processeur génère automatiquement des statistiques :

```
total_exercises: 873         # Nombre d'exercices chargés
valid_exercises: 873         # Nombre d'exercices valides
invalid_exercises: 0         # Nombre d'exercices rejetés
duplicates_removed: 0        # Nombre de doublons supprimés
fields_cleaned: 5            # Nombre de champs nettoyés
```

---

## 🔧 Règles de Validation

### Champs obligatoires
- `name` : Nom de l'exercice (non vide)
- `id` : Identifiant unique (non vide)
- `category` : Catégorie d'exercice
- `equipment` : Équipement nécessaire
- `primaryMuscles` : Muscles principaux (liste)

### Valeurs autorisées

**Niveaux (level) :**
- `beginner`, `intermediate`, `expert`
- Valeur par défaut si invalide : `intermediate`

**Catégories (category) :**
- `cardio`, `olympic weightlifting`, `plyometrics`
- `powerlifting`, `strength`, `stretching`, `strongman`
- Valeur par défaut si invalide : `strength`

**Types de mouvement (calculé) :**
- `push` : Mouvements de poussée
- `pull` : Mouvements de tirage
- `cardio` : Exercices cardiovasculaires
- `stretching` : Étirements
- `other` : Autres types

---

## 🛠️ Personnalisation

### Ajouter un nouveau processeur

1. Créer un dossier dans `src/processors/` (ex: `fitness_tracker/`)

2. Créer les fichiers du module :

```python
# src/processors/fitness_tracker/__init__.py
from .processor import FitnessTrackerProcessor
from .validators import FitnessTrackerValidator
from .cleaners import FitnessTrackerCleaner
from .enrichers import FitnessTrackerEnricher

__all__ = ['FitnessTrackerProcessor', 'FitnessTrackerValidator', 
           'FitnessTrackerCleaner', 'FitnessTrackerEnricher']

# src/processors/fitness_tracker/processor.py
from src.processors.base_processor import BaseProcessor
from .validators import FitnessTrackerValidator
from .cleaners import FitnessTrackerCleaner
from .enrichers import FitnessTrackerEnricher

class FitnessTrackerProcessor(BaseProcessor):
    def __init__(self):
        super().__init__("FitnessTrackerProcessor")
    
    def validate_data(self, df):
        return FitnessTrackerValidator.validate(df)
    
    def clean_data(self, df):
        return FitnessTrackerCleaner.clean(df)
    
    def enrich_data(self, df):
        return FitnessTrackerEnricher.enrich_all(df)
    # ...
```

3. Ajouter dans `run_processing.py` :

```python
from src.processors.fitness_tracker import FitnessTrackerProcessor

def process_fitness_tracker():
    processor = FitnessTrackerProcessor()
    # ...
    return processor.run(input_file)

# Dans main()
results['fitness_tracker'] = process_fitness_tracker()
```

---

## 📋 Format CSV Exporté

Les listes sont converties en chaînes séparées par `|` :

| Champ | Format | Exemple |
|-------|--------|---------|
| `primaryMuscles` | String avec \| | "chest\|triceps" |
| `secondaryMuscles` | String avec \| | "shoulders" |
| `all_muscles` | String avec \| | "chest\|triceps\|shoulders" |
| `instructions` | String avec \| | "Step 1\|Step 2\|Step 3" |
| `images` | String avec \| | "image1.jpg\|image2.jpg" |

---

## ✅ Checklist de Qualité

Après traitement, vérifiez :

- [ ] Aucun champ obligatoire vide
- [ ] Tous les niveaux dans la liste autorisée
- [ ] Toutes les catégories valides
- [ ] Aucun doublon (par id ou name)
- [ ] Métadonnées de traçabilité présentes
- [ ] Formats d'export (JSON + CSV) générés
- [ ] Statistiques cohérentes

---

## 🐛 Résolution de Problèmes

### Erreur : "Aucun fichier brut trouvé"
**Solution :** Exécuter d'abord le scraping
```bash
python -m src.scrapers.exercisedb_scraper
```

### Erreur : Permission refusée sur fichier
**Solution :** Fermer le fichier dans Excel/éditeur et réessayer

### Données incohérentes
**Solution :** Vérifier les logs dans `data/logs/etl.log`

---

## 📊 Prochaines Étapes

1. ✅ **Exercices ExerciseDB** - FAIT (module `exercises/`)
2. ✅ **Profils utilisateurs Gym Members** - FAIT (module `gym_members/`)
3. 🔄 **Nutrition** - Structure prête (module `nutrition/`)
4. ⏳ **Fitness Tracker** - À faire

Une fois tous les processeurs créés, vous pourrez :
- Concevoir le modèle de base de données
- Implémenter les loaders SQLAlchemy
- Créer l'API REST

---

**Dernière mise à jour :** 15 janvier 2026

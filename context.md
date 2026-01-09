# Cahier des Charges - MSPR HealthAI Coach

## 📋 Informations générales

**Programme** : Concepteur Développeur d'Applications / Certification Professionnelle Développeur en Intelligence Artificielle et Data Science  
**Référence** : RNCP36581 - Bloc E6.1  
**Projet** : Création d'un backend métier permettant le nettoyage et la visualisation des données

---

## 📚 Table des matières

1. [Compétences évaluées](#-compétences-évaluées)
2. [Modalités d'évaluation](#-modalités-dévaluation)
3. [Contexte du projet](#-i--contexte)
4. [Cahier des charges](#-ii--cahier-des-charges)
5. [Besoins exprimés](#-iii--besoins-exprimés-par-healthai-coach)
6. [Livrables attendus](#-iv--livrables-attendus)
7. [Ressources fournies](#-v--ressources-fournies)

---

## 🎯 Compétences évaluées

### Compétences principales (Data Science)

- ✅ Définir les sources et les outils nécessaires pour permettre de collecter les données
- ✅ Recueillir de manière sécurisée les informations à partir de sources adaptées (sources hétérogènes, internes ou Open Data)
- ✅ Paramétrer les outils afin d'importer les données de manière automatisée et sécurisée
- ✅ Analyser, nettoyer, trier et s'assurer de la qualité des données afin de les rendre exploitables pour la solution I.A
- ✅ Construire la structure de stockage des données (modèle de données) répondant aux besoins d'analyse
- ✅ Représenter graphiquement les relations entre les données via des tableaux de bord accessibles
- ✅ Exploiter et analyser les informations via requêtage pour répondre aux exigences de la solution IA

### Compétences supplémentaires (CDA)

- ✅ Installer et configurer son environnement de travail en fonction du projet
- ✅ Développer des interfaces utilisateur
- ✅ Développer des composants métiers

---

## 📝 Modalités d'évaluation

### Organisation du projet

- **Durée de préparation** : 19 heures
- **Travail d'équipe** : 4 apprenants (5 maximum si groupe impair)

### Phase 1 : Préparation

**Objectif** : Démontrer l'acquisition des compétences visées par ce bloc  
**Moyen** : Support de présentation

### Phase 2 : Soutenance orale collective

**Durée totale** : 50 minutes réparties comme suit :
- **20 minutes** : Soutenance orale par l'équipe
- **30 minutes** : Entretien collectif avec le jury (questionnement complémentaire)

**Composition du jury** : 2 évaluateurs n'ayant pas participé à la formation et ne connaissant pas les apprenants

---

## 🏢 I – Contexte

### Présentation de HealthAI Coach

**HealthAI Coach** est une jeune startup française positionnée sur le marché en pleine expansion de la **santé connectée** et du **coaching personnalisé**. Son ambition est de proposer une plateforme digitale intégrant :
- Suivi nutritionnel
- Accompagnement sportif
- Surveillance d'indicateurs de santé

### 1. Business model

L'entreprise a adopté un **modèle économique hybride** :

| Offre | Prix | Fonctionnalités |
|-------|------|-----------------|
| **Freemium** | Gratuit | Journal alimentaire, suivi d'activité, calcul d'IMC, tableaux de progression simples |
| **Premium** | 9,99 €/mois | Recommandations IA personnalisées, plans nutritionnels et sportifs détaillés, suivi approfondi des objectifs |
| **Premium+** | 19,99 €/mois | Intégration données biométriques (fréquence cardiaque, sommeil, poids), consultations en ligne avec nutritionnistes partenaires |
| **B2B** | Variable | Distribution en marque blanche pour salles de sport, mutuelles et entreprises |

### 2. Cibles principales

- 👥 **Millennials et Génération Z** (25-35 ans) : soucieux de leur santé et habitués aux outils numériques
- 🏙️ **Urbains actifs** : disposant de peu de temps pour un suivi personnalisé
- 🎯 **Débutants** en nutrition et sport : recherchant des conseils fiables et structurés
- 🎖️ **Personnes avec objectifs spécifiques** : perte de poids, renforcement musculaire, amélioration du sommeil

### 3. Enjeux du marché et concurrence

**Contexte du marché** :
- Croissance mondiale : **+20% par an**
- Stimulée par l'adoption massive des objets connectés
- Sensibilisation accrue aux problématiques de santé préventive

**Concurrents** : MyFitnessPal, Yazio, Fitbit Premium (focus sur le suivi quantitatif)

**Différenciation de HealthAI Coach** :
- ✨ Intégration d'IA générative et prédictive pour recommandations personnalisées
- 🔄 Suivi global et holistique (nutrition, sport, sommeil, biométrie)
- 💡 Approche accessible via modèle freemium inclusif
- 🤝 Stratégie B2B en marque blanche

### 4. Écosystème technologique

```
┌─────────────────────────────────────────────┐
│     Application mobile iOS/Android          │
├─────────────────────────────────────────────┤
│     API REST sécurisée                      │
├─────────────────────────────────────────────┤
│     Backend métier central                  │
│  (collecte, nettoyage, stockage données)    │
├─────────────────────────────────────────────┤
│     Tableaux de bord analytiques            │
├─────────────────────────────────────────────┤
│     Modules IA (recommandation/prédiction)  │
└─────────────────────────────────────────────┘
```

**Objectifs du socle technique** :
- ✅ Fiabilité et évolutivité
- ✅ Industrialisable
- ✅ Capable d'absorber une volumétrie croissante
- ✅ Garantir qualité, sécurité et accessibilité

---

## 📋 II – Cahier des charges

### Mission confiée

Concevoir, développer et livrer le **backend métier** de la plateforme HealthAI Coach :

1. **Collecte automatisée** : Système d'intégration de différentes sources de données avec contraintes de sécurité et fiabilité
2. **Transformation et nettoyage** : Processus garantissant l'exploitabilité des données (qualité, cohérence, complétude)
3. **Base de données relationnelle** : Conception et implémentation adaptées aux besoins, avec documentation et scripts de migration
4. **API REST** : Permettant aux applications front-end et équipes internes de consulter et exploiter les données
5. **Interface de visualisation** : Accessible pour suivre les indicateurs clés

### Objectifs

**Double objectif** :
1. 📊 Disposer d'un référentiel fiable pour les futurs travaux en IA (recommandations personnalisées)
2. 📈 Fournir aux équipes produit un tableau de bord interactif pour visualiser les indicateurs essentiels

**Exigences** :
- ⚙️ Automatisé, sécurisé et reproductible
- 🔧 Réduction des interventions manuelles
- 🚀 Faciliter le déploiement dans différents environnements
- 📦 Conçu pour évoluer et servir de base aux futurs micro-services

---

## 🎯 III – Besoins exprimés par HealthAI Coach

### 1. Ingestion et traitement de données

**Pipeline d'ingestion automatisé** capable de :
- 📥 Importer régulièrement des datasets externes (formats CSV, JSON, XLSX)
- ✔️ Valider automatiquement la structure et la cohérence des données
- ⚠️ Gérer les erreurs dans les sources de données

**Données concernées** :
- 👤 Profils utilisateurs (âge, objectifs, contraintes spécifiques)
- 🍎 Base nutritionnelle (aliments, macronutriments, recettes)
- 🏋️ Catalogue d'exercices (types, niveaux de difficulté, équipements requis)
- 📊 Métriques de performance (progression, données biométriques simulées : poids, sommeil, fréquence cardiaque)

### 2. Interface d'administration et API de gestion

**Interface web d'administration** permettant :
- 📊 Dashboard de pilotage en temps réel avec métriques de qualité
- 🛠️ Outils de nettoyage interactifs pour corrections manuelles
- ✅ Workflow de validation et d'approbation avant mise en production
- 📤 Export des données nettoyées (formats JSON ou CSV)

**API REST de gestion** :
- 🔐 Sécurisée et documentée via OpenAPI
- 🔄 Manipulation programmatique des données (CRUD utilisateurs, alimentation, exercices, progression)
- 🚀 Conçue pour évoluer avec futurs modules IA et front-end mobile

### 3. Analytics et visualisation business

**Module analytique** générant :
- 👥 Métriques utilisateurs (répartition par âge, objectifs, taux de progression)
- 🍽️ Analyses nutritionnelles (tendances alimentaires, déficits/excès par profil)
- 💪 Statistiques fitness (exercices les plus pratiqués, niveaux d'intensité)
- 📈 KPIs business (engagement, conversion premium, satisfaction)

**Tableau de bord interactif** :
- ♿ Conforme aux standards d'accessibilité (RGAA niveau AA)
- 👨‍🔬 Compréhensible par data scientists et décideurs non techniques

### 4. Exigences complémentaires

- 📄 Données disponibles au format JSON ou CSV
- 📝 Justification du choix des datasets utilisés
- 🔧 Solution générique et extensible
- ✅ Minimum requis : chaîne complète sur au moins 2 sources de données
- 🏭 Logique industrielle, prêt à être intégré dans l'écosystème

---

## 📦 IV – Livrables attendus

### 1. Documentation des données et flux

**Rapport d'inventaire** :
- 📋 Recensement de toutes les sources (internes et externes)
- 📊 Origine, format, fréquence de mise à jour
- ✅ Règles de qualité appliquées

**Diagramme des flux** :
- 🔄 Visualisation du cheminement : collecte → traitement → stockage → exposition API

### 2. Pipelines ETL opérationnels

- 💻 Code source complet, versionné et commenté
- ⏰ Scripts de planification (cron, Airflow, ou équivalent)
- 📝 Système de gestion des erreurs et logs

### 3. Jeux de données nettoyés et exploitables

- 🧹 Dataset consolidé et sans anomalies
- 📚 Référence pour l'évaluation de la qualité des pipelines
- 🤖 Base de travail pour futurs modules d'IA

### 4. Base de données relationnelle et scripts associés

**Modèle de données** :
- 📐 Documenté au format Merise (MCD/MLD/MPD) ou UML
- 💾 Scripts SQL de création et de migration
- 🔄 Structure pérenne, versionnée et reproductible

### 5. API REST documentée

- 🔐 API REST fonctionnelle et sécurisée
- 🔄 Opérations CRUD (utilisateurs, alimentation, exercices, métriques)
- 📖 Documentation complète au format OpenAPI
- ✅ Testée et prête pour adoption par équipes front-end et partenaires

### 6. Interface web et tableau de bord interactif

**Interface d'administration** :
- 🌐 Accessible par navigateur
- 👀 Visualisation des flux de données
- ✏️ Validation et correction des anomalies
- 📤 Export des données nettoyées

**Tableau de bord** :
- 📊 Indicateurs clairs (qualité données, progression utilisateurs, tendances)
- ♿ Respect standards d'accessibilité numérique (RGAA niveau AA)

### 7. Rapport technique et guide de déploiement

**Rapport technique** (5-8 pages) :
- 📝 Contexte et démarche
- 🛠️ Choix technologiques
- 📊 Résultats obtenus
- ⚠️ Difficultés rencontrées
- 🔮 Perspectives d'évolution

**Guide de déploiement** :
- 🐳 Procédure détaillée (Docker/Docker Compose)
- ⚙️ Variables d'environnement
- 📋 Prérequis logiciels
- ⏱️ Déploiement en moins de 30 minutes

### 8. Support de soutenance

- 📽️ Support de présentation pour soutenance finale
- 📊 Synthèse du travail réalisé
- 🎯 Démarche, difficultés, solutions, résultats et perspectives

### ⚠️ Important

**L'évaluation repose sur 3 éléments** :
1. ✅ Qualité du travail réalisé
2. 📦 Pertinence et exhaustivité des livrables
3. 🎤 Capacité à présenter, justifier et valoriser le travail lors de la soutenance

---

## 🗂️ V – Ressources fournies

### 1. Jeux de données de référence

#### 🍎 Base nutritionnelle

**Daily Food & Nutrition Dataset**
- 🔗 [Kaggle Dataset](https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset)
- 📊 Données : apports quotidiens, valeurs nutritionnelles, tracking santé

**Diet Recommendations Dataset**
- 🔗 [Kaggle Dataset](https://www.kaggle.com/datasets/ziya07/diet-recommendations-dataset)
- 📊 Données : profils santé, besoins diététiques, recommandations IA

#### 🏋️ Catalogue d'exercices

**ExerciseDB API Repository** (1300+ exercices)
- 🔗 [GitHub Repository](https://github.com/ExerciseDB/exercisedb-api/tree/main)
- 💡 Recommandation : Fork du repository sur votre compte GitHub personnel
- 📊 Données : nom, type, muscle groups, équipement, niveau, images, instructions

#### 👤 Profils utilisateurs

**Gym Members Exercise Dataset** (973 échantillons)
- 🔗 [Kaggle Dataset](https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset)
- 📊 Données : âge, genre, poids, taille, BPM max/moyen, calories, BMI, body fat %

**Fitness Tracker Dataset** (données d'activité quotidienne)
- 🔗 [Kaggle Dataset](https://www.kaggle.com/datasets/nadeemajeedch/fitness-tracker-dataset)
- 📊 Données : steps, calories burn, minutes d'activité, profils diversifiés

### 2. Assistance et périmètre

⚠️ **Important** : Dans le cadre de ce projet pédagogique :
- 🚫 Aucun contact direct avec HealthAI Coach
- 📋 Le cahier des charges constitue la seule expression officielle du besoin
- 👨‍🏫 Clarifications via l'encadrant pédagogique (rôle du client)

### 3. Webographie

#### Documentation technique

**Data Processing & ETL**
- 🐼 [Documentation Pandas](https://pandas.pydata.org/pandas-docs/stable/)
- 🔧 [Guide ETL Apache Hop](https://hop.apache.org/manual/latest/getting-started/)
- 🔧 [Guide ETL Talend](https://www.talend.com/fr/resources/guide-etl/)

**Base de données**
- 🐘 [Documentation PostgreSQL](https://www.postgresql.org/docs/)

**Visualisation**
- 📊 [Documentation Power BI](https://docs.microsoft.com/fr-fr/power-bi/)
- 📊 [Documentation Apache Superset](https://superset.apache.org/docs/intro)
- 📊 [Documentation Grafana](https://grafana.com/docs/)
- 📊 [Guide Metabase](https://www.metabase.com/docs/latest/)

**Datasets**
- 🗂️ [Datasets Kaggle](https://www.kaggle.com/datasets/)

---

**Document préparé pour : EPSI - MSPR Bloc E6.1**  
**Date : Janvier 2026**

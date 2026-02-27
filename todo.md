Refacto to Do:

1) Ne plus gérer un load par pipeline, mais à la place:

-Aggréger toutes les données processed et les aggréger dans un seul csv. IMPORTANT: ce CSV devra forcément
répondre EXACTEMENT au schéma de la bdd (si données absentes, garder les colonnes)
-Et Load ce csv dans la bdd postgre.

Les pipelines par source ne prendront en charge que l'extract des données et les transform en donneées_processed.csv.

2) Modifier le logger pour avoir le détail des erreurs dans les logs. Et par conséquent modifier l'odre des logs pour avoir un log pour le load final.

3) Ranger les utils et éviter les méthodes doublons

4) Gérer les uuid pour les gym-members et body-performance pipeline


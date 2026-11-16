# BiblioIIT - Gestion de la Bibliothèque

Projet d'application console modulaire en Python pour la gestion de la bibliothèque de l'Institut Ivoirien de Technologie (IIT).

## Architecture du projet

Le projet est structuré selon une séparation claire des responsabilités :

- `modeles.py` : Définition des structures de données (`Livre`, `Emprunt`).
- `regles.py` : Règles de gestion métier (durées, calcul de retour, détection des retards, vérification de disponibilité).
- `depot_sqlite.py` : Couche d'accès aux données avec SQLite.
- `service.py` : Logique applicative orchestrant les dépôts et les règles.
- `console.py` : Interface utilisateur en ligne de commande (menu interactif).
- `tests/` : Suite de tests unitaires pour valider chaque composant.

## Installation et lancement

1. Installer les dépendances de test :
   ```bash
   pip install -r requirements.txt
   ```

2. Lancer l'application :
   ```bash
   python console.py
   ```

3. Exécuter les tests :
   ```bash
   pytest
   ```

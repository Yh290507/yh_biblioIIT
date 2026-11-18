# BiblioIIT — Système de Gestion de Bibliothèque Universitaire (SIGB)

> **Institut Ivoirien de Technologie (IIT)**  
> **Module de Génie Logiciel & Programmation Python — Projet de Session**  
> *Application console modulaire, architecture en couches (Clean / Service-Repository), règles métier réelles et tests automatisés.*

---

## 1. Présentation du Projet

**BiblioIIT** est une solution logicielle conçue pour automatiser et fiabiliser la gestion documentaire, les usagers et les opérations d'emprunt de la bibliothèque universitaire de l'**Institut Ivoirien de Technologie (IIT)**.

Inspirée des systèmes professionnels de gestion de bibliothèques (**SIGB**), l'application permet aux étudiants et au personnel gestionnaire de :
1. **Rechercher des ouvrages** dans un fonds de référence de littérature africaine par mot-clé (titre, auteur, catégorie), avec affichage dynamique du statut de disponibilité et des exemplaires.
2. **Gérer les usagers (Lecteurs)** : fichier complet des étudiants inscrits (matricule, nom, prénom, filière, contact).
3. **Enregistrer des emprunts sécurisés** : calcul automatique de l'échéance à 14 jours, limitation à un quota de 3 livres maximum par étudiant, interdiction d'emprunter des doublons d'un même titre et blocage strict si l'étudiant a des retards non régularisés.
4. **Restituer des livres** avec réintégration instantanée au stock disponible et notification d'avertissement en cas de retard.
5. **Suivre et exporter les retards** : détection des échéances dépassées et génération d'un rapport administratif au format CSV compatible Excel.
6. **Piloter le fonds documentaire** : tableau de bord statistique complet (taux de rotation, ratio de disponibilité, nombre d'emprunts actifs).
7. **Paramétrer le système sans recompilation** : fichier de configuration externe `config.json`.

---

## 2. Architecture Logicielle & Justification Technique

Le projet adopte une **Architecture en Couches (Layered / Clean Architecture)** basée sur le patron de conception **Service-Repository**, une variante moderne et découplée du classique **MVC (Modèle-Vue-Contrôleur)**.

### Schéma des flux et dépendances

```text
┌────────────────────────────────────────────────────────┐
│             INTERFACE UTILISATEUR (VUE)                │
│                      console.py                        │
└──────────────────────────┬─────────────────────────────┘
                           │ Appelle les cas d'usage
                           ▼
┌────────────────────────────────────────────────────────┐
│             LOGIQUE APPLICATIVE (CONTRÔLEUR)           │
│                      service.py                        │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
   Valide avec │              Persiste via│
               ▼                          ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│      RÈGLES MÉTIER       │  │   COUCHE DE DONNÉES      │
│        regles.py         │  │     depot_sqlite.py      │
│     (et config.json)     │  │      (biblio.db)         │
└──────────────┬───────────┘  └───────────┬──────────────┘
               │                          │
               └───────────┬──────────────┘
                           │ Manipulent
                           ▼
┌────────────────────────────────────────────────────────┐
│               STRUCTURES DE DONNÉES                    │
│                      modeles.py                        │
│               (Livre, Lecteur, Emprunt)                │
└────────────────────────────────────────────────────────┘
```

### Correspondance avec le patron MVC

| Fichier du projet | Rôle MVC classique | Responsabilité exacte |
| :--- | :--- | :--- |
| **`console.py`** | **Vue (View)** | Présentation dans le terminal, menus ergonomiques, saisies sécurisées et affichage soigné. |
| **`service.py`** | **Contrôleur (Controller)** | Orchestration des cas d'usage : relie l'interface, les règles métier, la persistance et l'export CSV. |
| **`regles.py`** | **Modèle Métier (Domain Rules)** | Règles pures : durée de prêt, quotas par usager, contrôle des retards, exceptions métier typées. |
| **`depot_sqlite.py`** | **Modèle Données (Repository)** | Gestion de la base de données relationnelle SQLite, requêtes SQL (CRUD) et intégrité référentielle. |
| **`modeles.py`** | **Entités (Data Entities)** | Définition des objets métier (`Livre`, `Lecteur`, `Emprunt`). |
| **`config.json`** | **Configuration** | Paramètres métier externes (durée de prêt, quotas, blocages). |
| **`tests/`** | **Qualité (Pipeline Vert)** | Suite de 19 tests automatisés validant unitairement et en intégration l'ensemble du système. |

---

## 3. Détail des Règles de Gestion (RG) Réelles

1. **RG 1 — Durée de prêt réglementaire :** 14 jours calendaires calculés automatiquement à partir de la date d'emprunt (modifiable dans `config.json`).
2. **RG 2 — Quota maximal d'emprunt :** Un étudiant ne peut avoir plus de **3 livres** simultanément en cours de prêt.
3. **RG 3 — Règle du retardataire bloqué :** Un étudiant ayant un prêt non restitué dont l'échéance est dépassée ne peut contracter aucun nouvel emprunt.
4. **RG 4 — Non-doublon d'emprunt :** Un usager ne peut pas emprunter deux exemplaires du même titre en même temps.
5. **RG 5 — Disponibilité multi-exemplaires :** Un livre reste empruntable tant qu'il reste au moins un exemplaire disponible en rayon.
6. **RG 6 — Intégrité et non-suppression :** Tout livre ou lecteur ayant un historique de prêt enregistré en base ne peut pas être supprimé (préservation des archives comptables).
7. **RG 7 — Avertissement au retour :** Toute restitution effectuée au-delà de la date prévue affiche une alerte avec le nombre exact de jours de dépassement.

---

## 4. Scénario de Démonstration (Session Réelle de Cours)

L'application reproduit fidèlement la session démontrée en classe :

1. **Recherche (Choix 1)** :
   - Saisie : `Kourouma`
   - Résultat : Liste `L002  Les Soleils des indépendances (1968)` et `L004  Allah n'est pas obligé (2000)`.
2. **Premier emprunt (Choix 2)** :
   - Saisie : Code `L002`, Matricule `E2026-001`.
   - Résultat : Emprunt validé avec date de retour prévue calculée à $J + 14$.
3. **Tentative de ré-emprunt (Choix 2)** :
   - Saisie : Code `L002`, Matricule `E2026-002`.
   - Résultat : Blocage immédiat avec le message `Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté`.
4. **Suivi des retards (Choix 4)** :
   - Affiche les emprunts échus avec nom, filière, contact et décompte des jours.
5. **Restitution (Choix 3)** :
   - Saisie : Code `L002`.
   - Résultat : Clôture de l'emprunt et remise en rayon de l'exemplaire.

---

## 5. Stratégie de Tests & « Pipeline Vert »

Le projet intègre **19 tests automatisés** répartis dans le dossier `tests/`, garantissant zéro régression :

- `tests/test_modeles.py` : Entités `Livre`, `Lecteur`, `Emprunt`.
- `tests/test_regles.py` : Calculs de date, détection des retards, quotas et non-doublons.
- `tests/test_depot.py` : Requêtes SQL, recherche, emprunts et retours SQLite.
- `tests/test_service.py` : Scénario complet de bout en bout, statistiques, protection de suppression et export CSV.

### Exécution des tests

```bash
python -m unittest discover tests
```

> **Résultat :** `Ran 19 tests in 0.34s - OK` (Pipeline 100 % vert).

---

## 6. Lancement Rapide

### Prérequis
- Python 3.10 ou version supérieure (testé sous Python 3.13).
- Bibliothèque standard uniquement (aucun `pip install` requis).

### Lancement de l'application
Dans votre terminal :

```bash
python console.py
```

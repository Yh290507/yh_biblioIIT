# BiblioIIT — Système de Gestion de Bibliothèque

> **Institut Ivoirien de Technologie (IIT)**  
> **Module de Génie Logiciel & Programmation Python — Séance 4**  
> *Application console modulaire, versionnée professionnellement et testée.*

---

## 1. Présentation du Projet

**BiblioIIT** est une solution logicielle conçue pour automatiser et fiabiliser la gestion documentaire et les opérations d'emprunt de la bibliothèque universitaire de l'**Institut Ivoirien de Technologie (IIT)**.

L'application permet aux étudiants et gestionnaires de :
1. **Rechercher des ouvrages** dans le catalogue par mot-clé (titre ou auteur), avec affichage dynamique du statut de disponibilité.
2. **Enregistrer des emprunts** avec calcul automatique de la date de restitution à 14 jours et blocage strict si l'ouvrage est déjà sorti.
3. **Restituer des livres** pour les réintégrer instantanément au fonds disponible.
4. **Suivre les retards** grâce à un moteur de détection des échéances dépassées calculant le nombre exact de jours de pénalité.

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
└──────────────┬───────────┘  └───────────┬──────────────┘
               │                          │
               └───────────┬──────────────┘
                           │ Manipulent
                           ▼
┌────────────────────────────────────────────────────────┐
│               STRUCTURES DE DONNÉES                    │
│                      modeles.py                        │
└────────────────────────────────────────────────────────┘
```

### Correspondance avec le patron MVC

| Fichier du projet | Rôle MVC classique | Responsabilité exacte |
| :--- | :--- | :--- |
| **`console.py`** | **Vue (View)** | Présentation dans le terminal, menus ergonomiques, saisies sécurisées et affichage des messages. |
| **`service.py`** | **Contrôleur (Controller)** | Orchestration des cas d'usage : relie l'interface, les règles métier et la persistance. |
| **`regles.py`** | **Modèle Métier (Domain Rules)** | Règles pures : durée de 14 jours, calcul des dates, détection des retards, exceptions d'indisponibilité. |
| **`depot_sqlite.py`** | **Modèle Données (Repository)** | Gestion de la base de données relationnelle SQLite, requêtes SQL (CRUD) et intégrité référentielle. |
| **`modeles.py`** | **Entités (Data Entities)** | Définition des objets de transfert de données (`Livre`, `Emprunt`). |
| **`tests/`** | **Qualité (Pipeline Vert)** | Suite de tests automatisés validant chaque couche unitairement et en intégration. |

---

## 3. Détail Fonctionnel des Modules

### A. `modeles.py` — Entités de données
- **Classe `Livre`** : Encapsule les attributs d'un ouvrage (`code`, `titre`, `auteur`, `annee`, `disponible`). Sa méthode `__str__()` garantit un affichage standardisé conforme au cours (ex. : `L004  Allah n'est pas obligé - Ahmadou Kourouma (2000)`).
- **Classe `Emprunt`** : Représente un prêt (`id`, `code_livre`, `matricule`, `date_emprunt`, `date_retour_prevue`, `date_retour_effective`). La méthode `est_en_cours()` indique si l'ouvrage est actuellement entre les mains d'un lecteur.

### B. `regles.py` — Règles de gestion métier
- **Délai réglementaire** : Défini par la constante `DUREE_EMPRUNT_JOURS = 14`.
- **Calcul d'échéance** : La fonction `calculer_date_retour()` ajoute automatiquement 14 jours à la date de prêt.
- **Contrôle des retards** : Les fonctions `est_en_retard()` et `calculer_jours_retard()` évaluent si la date d'échéance est franchie pour un emprunt non clôturé.
- **Exceptions métier typées** : 
  - `LivreDejaEmprunteError` : Lève le message exact requis par le sujet :  
    `Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté`
  - `LivreIntrouvableError` : Sécurise les saisies de codes inexistants.
  - `EmpruntIntrouvableError` : Empêche la restitution d'un livre non emprunté.

### C. `depot_sqlite.py` — Persistance SQLite
- **Fichier de base** : `biblio.db` (généré automatiquement à la racine).
- **Intégrité référentielle** : Activation explicite des clés étrangères via `PRAGMA foreign_keys = ON;`.
- **Initialisation automatique** : Crée les tables `livres` et `emprunts` dès le premier lancement.
- **Fonds initial pré-chargé** : Insère 25 ouvrages de référence de la littérature africaine et ivoirienne (*Ahmadou Kourouma*, *Bernard Dadié*, *Cheikh Hamidou Kane*, *Chinua Achebe*, *Mariama Bâ*, *Camara Laye*, *Amadou Hampâté Bâ*, etc.).
- **Méthodes optimisées** : Recherche insensible à la casse (`LOWER() LIKE %...%`), transactions protégées avec gestionnaires de contexte (`with conn:`).

### D. `service.py` — Logique applicative
- **Injection de dépendance** : Le constructeur `BibliothequeService(depot=None)` permet d'injecter un dépôt temporaire ou en mémoire pour des tests isolés.
- **Double vérification de sécurité** : Avant tout emprunt, le service interroge le dépôt, passe la vérification à `regles.py`, puis commande l'enregistrement SQL atomique.

### E. `console.py` — Interface utilisateur
- **Boucle interactive robuste** : Protégée contre les saisies invalides et les interruptions volontaires (`Ctrl+C`, `EOF`).
- **Affichage soigné** : Utilise des cadres Unicode (`┌`, `─`, `│`, `└`) et des tableaux alignés pour une lisibilité maximale dans tout terminal.

---

## 4. Scénario d'Exécution Complet (Session du Professeur)

L'application reproduit fidèlement la session démontrée en classe :

1. **Recherche (Choix 1)** :
   - Saisie : `Kourouma`
   - Résultat : Liste `L002  Les Soleils des indépendances (1968)` et `L004  Allah n'est pas obligé (2000)`.
2. **Premier emprunt (Choix 2)** :
   - Saisie : Code `L002`, Matricule `E2026-001`.
   - Résultat : Emprunt validé avec date de retour prévue calculée à J + 14.
3. **Tentative de ré-emprunt (Choix 2)** :
   - Saisie : Code `L002`, Matricule `E2026-002`.
   - Résultat : Blocage immédiat avec le message `Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté`.
4. **Suivi des retards (Choix 4)** :
   - Affiche les emprunts dont l'échéance est échue avec le nom du livre, l'étudiant et le décompte des jours.
5. **Restitution (Choix 3)** :
   - Saisie : Code `L002`.
   - Résultat : Clôture de l'emprunt et remise à disposition immédiate du livre.
6. **Sortie (Choix 0)** :
   - Quitte proprement l'application.

---

## 5. Stratégie de Tests & « Pipeline Vert »

Le projet intègre **11 tests automatisés** répartis dans le dossier `tests/`, couvrant unitairement et en intégration l'ensemble du système :

- `tests/test_modeles.py` : Validation des entités et formats d'affichage.
- `tests/test_regles.py` : Validation des règles de calcul, retards et blocages.
- `tests/test_depot.py` : Validation des écritures et requêtes SQLite en environnement temporaire isolé.
- `tests/test_service.py` : Validation du scénario complet de bout en bout.

### Exécution immédiate des tests

Les tests sont compatibles à 100 % avec la bibliothèque standard Python (aucune dépendance externe requise) ainsi qu'avec `pytest` :

```bash
# Méthode 1 : Avec le moteur natif Python unittest (recommandé, zéro installation) :
python -m unittest discover tests

# Méthode 2 : Avec pytest :
pytest
```

> **Résultat garanti :** `Ran 11 tests in 0.106s - OK` (Pipeline vert).

---

## 6. Historique & Versionnement Git Professionnel

Le projet a été développé en appliquant un flux de travail rigoureux par branches fonctionnelles, respectant la convention de nommage des commits :

- `feature/modeles` : Définition des structures de données (`Livre`, `Emprunt`) et leurs tests.
- `feature/regles` : Implémentation des règles de calcul d'échéance et de gestion des conflits.
- `feature/base` : Intégration de la persistance SQLite et gestion du schéma relationnel.
- `feature/service` : Orchestration applicative et scénario d'intégration.
- `feature/menu` : Conception de l'interface console ergonomique.

Chaque branche a été validée, testée et fusionnée dans la branche principale `main`.  
Pour consulter l'historique complet :

```bash
git log --oneline --graph
```

---

## 7. Guide de Démarrage Rapide

### Prérequis
- Python 3.10 ou version supérieure (testé sous Python 3.13).
- SQLite3 (inclus par défaut dans toutes les distributions Python standard).

### Lancement de l'application
Dans votre terminal (ou dans le terminal intégré de Visual Studio Code) :

```bash
python console.py
```

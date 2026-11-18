"""
Module depot_sqlite.py - Couche d'accès aux données (persistance SQLite) pour BiblioIIT.
Gère les tables livres, lecteurs et emprunts selon le patron Repository.
"""

import sqlite3
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from modeles import Livre, Lecteur, Emprunt

DB_NAME = "biblio.db"

# Fonds de 25 ouvrages de référence en littérature africaine
# Format: (code, titre, auteur, annee, categorie, nb_exemplaires)
LIVRES_INITIAUX = [
    ("L001", "Climbié", "Bernard Dadié", 1956, "Roman autobiographique", 2),
    ("L002", "Les Soleils des indépendances", "Ahmadou Kourouma", 1968, "Roman classique", 1),
    ("L003", "L'Aventure ambiguë", "Cheikh Hamidou Kane", 1961, "Roman philosophique", 2),
    ("L004", "Allah n'est pas obligé", "Ahmadou Kourouma", 2000, "Roman contemporain", 2),
    ("L005", "Le monde s'effondre", "Chinua Achebe", 1958, "Roman historique", 3),
    ("L006", "Une si longue lettre", "Mariama Bâ", 1979, "Roman épistolaire", 2),
    ("L007", "L'Enfant noir", "Camara Laye", 1953, "Récit autobiographique", 3),
    ("L008", "L'Étrange Destin de Wangrin", "Amadou Hampâté Bâ", 1973, "Roman biographique", 2),
    ("L009", "Sous l'orage", "Seydou Badian", 1957, "Roman de société", 2),
    ("L010", "Rebelle", "Fatou Keïta", 1998, "Roman féministe", 2),
    ("L011", "Les Frasques d'Ébinto", "Amadou Koné", 1975, "Roman de jeunesse", 2),
    ("L012", "Le Pagne noir", "Bernard Dadié", 1955, "Contes traditionnels", 2),
    ("L013", "Un Nègre à Paris", "Bernard Dadié", 1959, "Chronique humoristique", 2),
    ("L014", "Le Pauvre Christ de Bomba", "Mongo Beti", 1956, "Roman satirique", 2),
    ("L015", "Ville cruelle", "Eza Boto", 1954, "Roman engagé", 2),
    ("L016", "Cahier d'un retour au pays natal", "Aimé Césaire", 1939, "Poésie / Négritude", 2),
    ("L017", "Batouala", "René Maran", 1921, "Roman (Prix Goncourt)", 1),
    ("L018", "La Rue Cases-Nègres", "Joseph Zobel", 1950, "Roman initiatique", 2),
    ("L019", "Cœur de caniche", "Isaïe Biton Koulibaly", 1989, "Nouvelles sentimentales", 2),
    ("L020", "Ah ! Les femmes...", "Isaïe Biton Koulibaly", 1999, "Chronique de société", 2),
    ("L021", "Le Baobab fou", "Ken Bugul", 1982, "Autobiographie", 1),
    ("L022", "Les Crapauds-broussards", "Tierno Monénembo", 1979, "Roman politique", 2),
    ("L023", "Verre Cassé", "Alain Mabanckou", 2005, "Roman picaresque", 2),
    ("L024", "Petit Pays", "Gaël Faye", 2016, "Roman contemporain", 3),
    ("L025", "La Plus Secrète Mémoire des hommes", "Mohamed Mbougar Sarr", 2021, "Roman (Prix Goncourt)", 2),
]

# Lecteurs initiaux de l'IIT
LECTEURS_INITIAUX = [
    ("E2026-001", "KOUASSI", "Jean-Marc", "0701020304", "Génie Logiciel"),
    ("E2026-002", "KOFFI", "Aminata", "0505060708", "Réseaux & Sécurité"),
    ("E2026-003", "DIARRASSOUBA", "Ibrahim", "0102030405", "Data Science & IA"),
    ("E2026-004", "TRAORE", "Fatoumata", "0788990011", "Génie Logiciel"),
    ("E2026-005", "YAO", "Christian", "0544332211", "Systèmes d'Information"),
    ("E2026-006", "BAMBA", "Sekou", "0711223344", "Génie Logiciel"),
    ("E2026-007", "KONE", "Mariam", "0566778899", "Management & SI"),
    ("E2026-008", "N'GUESSAN", "Franck", "0199887766", "Cybersécurité"),
    ("E2026-009", "TOURE", "Aïssata", "0733445566", "Data Science & IA"),
    ("E2026-010", "SYLLA", "Abdoulaye", "0522110033", "Réseaux & Télécoms"),
]


class DepotSqlite:
    """Gère toutes les interactions directes avec la base SQLite."""

    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self._initialiser_base()

    @contextmanager
    def _get_connection(self):
        """Ouvre une connexion avec activation des clés étrangères et fermeture garantie."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _initialiser_base(self):
        """Crée les tables nécessaires et insère le fonds initial de livres et usagers."""
        with self._get_connection() as conn:
            cur = conn.cursor()

            # Table des livres
            cur.execute("""
                CREATE TABLE IF NOT EXISTS livres (
                    code TEXT PRIMARY KEY,
                    titre TEXT NOT NULL,
                    auteur TEXT NOT NULL,
                    annee INTEGER NOT NULL,
                    disponible INTEGER DEFAULT 1,
                    categorie TEXT DEFAULT 'Littérature',
                    nb_exemplaires INTEGER DEFAULT 1
                );
            """)

            # Migration douce si la table existait déjà sans les nouvelles colonnes
            cur.execute("PRAGMA table_info(livres);")
            cols = [c["name"] for c in cur.fetchall()]
            if "categorie" not in cols:
                cur.execute("ALTER TABLE livres ADD COLUMN categorie TEXT DEFAULT 'Littérature';")
            if "nb_exemplaires" not in cols:
                cur.execute("ALTER TABLE livres ADD COLUMN nb_exemplaires INTEGER DEFAULT 1;")

            # Table des lecteurs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS lecteurs (
                    matricule TEXT PRIMARY KEY,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    contact TEXT,
                    filiere TEXT DEFAULT 'Génie Logiciel'
                );
            """)

            # Table des emprunts
            cur.execute("""
                CREATE TABLE IF NOT EXISTS emprunts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_livre TEXT NOT NULL,
                    matricule TEXT NOT NULL,
                    date_emprunt TEXT NOT NULL,
                    date_retour_prevue TEXT NOT NULL,
                    date_retour_effective TEXT,
                    FOREIGN KEY (code_livre) REFERENCES livres(code)
                );
            """)

            # Insérer les livres initiaux (sans doublons)
            for item in LIVRES_INITIAUX:
                code, titre, auteur, annee, cat, nb_ex = item
                cur.execute("""
                    INSERT INTO livres (code, titre, auteur, annee, disponible, categorie, nb_exemplaires)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                    ON CONFLICT(code) DO UPDATE SET
                        categorie=excluded.categorie,
                        nb_exemplaires=excluded.nb_exemplaires;
                """, (code, titre, auteur, annee, cat, nb_ex))

            # Insérer les lecteurs initiaux
            for item in LECTEURS_INITIAUX:
                mat, nom, prenom, tel, fil = item
                cur.execute("""
                    INSERT OR IGNORE INTO lecteurs (matricule, nom, prenom, contact, filiere)
                    VALUES (?, ?, ?, ?, ?);
                """, (mat, nom, prenom, tel, fil))

            conn.commit()

    # ==========================================================
    # GESTION DES LIVRES (CATALOGUE)
    # ==========================================================

    def _convertir_ligne_livre(self, row: sqlite3.Row, conn: sqlite3.Connection) -> Livre:
        """Convertit une ligne SQL en objet Livre avec calcul précis de disponibilité."""
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM emprunts WHERE code_livre = ? AND date_retour_effective IS NULL;",
            (row["code"],)
        )
        emprunts_en_cours = cur.fetchone()[0]
        nb_exemplaires = row["nb_exemplaires"] if "nb_exemplaires" in row.keys() else 1
        nb_dispos = max(0, nb_exemplaires - emprunts_en_cours)
        disponible = nb_dispos > 0

        return Livre(
            code=row["code"],
            titre=row["titre"],
            auteur=row["auteur"],
            annee=row["annee"],
            disponible=disponible,
            categorie=row["categorie"] if "categorie" in row.keys() else "Littérature",
            nb_exemplaires=nb_exemplaires,
            nb_disponibles=nb_dispos
        )

    def rechercher_livres(self, mot_cle: str) -> List[Livre]:
        """Recherche insensible à la casse par titre, auteur ou catégorie."""
        pattern = f"%{mot_cle.strip().lower()}%"
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT code, titre, auteur, annee, disponible, categorie, nb_exemplaires
                FROM livres
                WHERE LOWER(titre) LIKE ? OR LOWER(auteur) LIKE ? OR LOWER(categorie) LIKE ?
                ORDER BY code ASC;
            """, (pattern, pattern, pattern))
            rows = cur.fetchall()
            return [self._convertir_ligne_livre(r, conn) for r in rows]

    def obtenir_livre(self, code_livre: str) -> Optional[Livre]:
        """Récupère un livre par son code unique."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT code, titre, auteur, annee, disponible, categorie, nb_exemplaires
                FROM livres
                WHERE code = ?;
            """, (code_livre.strip().upper(),))
            row = cur.fetchone()
            if row:
                return self._convertir_ligne_livre(row, conn)
            return None

    def ajouter_livre(self, livre: Livre) -> Livre:
        """Ajoute un nouvel ouvrage au fonds documentaire."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO livres (code, titre, auteur, annee, disponible, categorie, nb_exemplaires)
                VALUES (?, ?, ?, ?, 1, ?, ?);
            """, (
                livre.code,
                livre.titre,
                livre.auteur,
                livre.annee,
                livre.categorie,
                livre.nb_exemplaires
            ))
            conn.commit()
            return livre

    def supprimer_livre(self, code_livre: str) -> bool:
        """Supprime un livre de la base (uniquement s'il n'a aucun historique d'emprunt)."""
        code = code_livre.strip().upper()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM livres WHERE code = ?;", (code,))
            conn.commit()
            return cur.rowcount > 0

    def lister_tous_les_livres(self) -> List[Livre]:
        """Retourne la totalité des ouvrages du catalogue."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT code, titre, auteur, annee, disponible, categorie, nb_exemplaires
                FROM livres
                ORDER BY code ASC;
            """)
            rows = cur.fetchall()
            return [self._convertir_ligne_livre(r, conn) for r in rows]

    # ==========================================================
    # GESTION DES LECTEURS (USAGERS / ÉTUDIANTS)
    # ==========================================================

    def ajouter_lecteur(self, lecteur: Lecteur) -> Lecteur:
        """Inscrit un nouvel étudiant à la bibliothèque."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO lecteurs (matricule, nom, prenom, contact, filiere)
                VALUES (?, ?, ?, ?, ?);
            """, (
                lecteur.matricule,
                lecteur.nom,
                lecteur.prenom,
                lecteur.contact,
                lecteur.filiere
            ))
            conn.commit()
            return lecteur

    def obtenir_lecteur(self, matricule: str) -> Optional[Lecteur]:
        """Recherche un lecteur par son matricule unique."""
        mat = matricule.strip().upper()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT matricule, nom, prenom, contact, filiere
                FROM lecteurs
                WHERE matricule = ?;
            """, (mat,))
            r = cur.fetchone()
            if r:
                return Lecteur(
                    matricule=r["matricule"],
                    nom=r["nom"],
                    prenom=r["prenom"],
                    contact=r["contact"],
                    filiere=r["filiere"]
                )
            return None

    def lister_lecteurs(self) -> List[Lecteur]:
        """Retourne l'ensemble des lecteurs enregistrés."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT matricule, nom, prenom, contact, filiere
                FROM lecteurs
                ORDER BY nom ASC, prenom ASC;
            """)
            rows = cur.fetchall()
            return [
                Lecteur(
                    matricule=r["matricule"],
                    nom=r["nom"],
                    prenom=r["prenom"],
                    contact=r["contact"],
                    filiere=r["filiere"]
                )
                for r in rows
            ]

    def rechercher_lecteurs(self, mot_cle: str) -> List[Lecteur]:
        """Recherche de lecteurs par matricule, nom, prénom ou filière."""
        pattern = f"%{mot_cle.strip().lower()}%"
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT matricule, nom, prenom, contact, filiere
                FROM lecteurs
                WHERE LOWER(matricule) LIKE ? OR LOWER(nom) LIKE ? OR LOWER(prenom) LIKE ? OR LOWER(filiere) LIKE ?
                ORDER BY nom ASC;
            """, (pattern, pattern, pattern, pattern))
            rows = cur.fetchall()
            return [
                Lecteur(
                    matricule=r["matricule"],
                    nom=r["nom"],
                    prenom=r["prenom"],
                    contact=r["contact"],
                    filiere=r["filiere"]
                )
                for r in rows
            ]

    def supprimer_lecteur(self, matricule: str) -> bool:
        """Supprime un lecteur de la base (si aucun historique d'emprunt)."""
        mat = matricule.strip().upper()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM lecteurs WHERE matricule = ?;", (mat,))
            conn.commit()
            return cur.rowcount > 0

    # ==========================================================
    # GESTION DES EMPRUNTS ET RESTITUTIONS
    # ==========================================================

    def enregistrer_emprunt(self, emprunt: Emprunt) -> Emprunt:
        """Sauvegarde un emprunt en base."""
        with self._get_connection() as conn:
            cur = conn.cursor()

            # Auto-inscription si le lecteur n'est pas encore enregistré
            cur.execute("""
                INSERT OR IGNORE INTO lecteurs (matricule, nom, prenom, contact, filiere)
                VALUES (?, 'Étudiant', ?, '', 'Génie Logiciel');
            """, (emprunt.matricule, emprunt.matricule))

            cur.execute("""
                INSERT INTO emprunts (code_livre, matricule, date_emprunt, date_retour_prevue, date_retour_effective)
                VALUES (?, ?, ?, ?, ?);
            """, (
                emprunt.code_livre,
                emprunt.matricule,
                emprunt.date_emprunt,
                emprunt.date_retour_prevue,
                emprunt.date_retour_effective
            ))
            emprunt.id = cur.lastrowid

            # Mise à jour de la disponibilité
            cur.execute("""
                SELECT nb_exemplaires FROM livres WHERE code = ?;
            """, (emprunt.code_livre,))
            row = cur.fetchone()
            nb_ex = row[0] if row else 1

            cur.execute("""
                SELECT COUNT(*) FROM emprunts WHERE code_livre = ? AND date_retour_effective IS NULL;
            """, (emprunt.code_livre,))
            en_cours = cur.fetchone()[0]

            if en_cours >= nb_ex:
                cur.execute("UPDATE livres SET disponible = 0 WHERE code = ?;", (emprunt.code_livre,))

            conn.commit()
            return emprunt

    def enregistrer_retour(self, code_livre: str, date_retour_effective: str) -> bool:
        """Clôture l'emprunt actif le plus ancien pour ce livre et réajuste la disponibilité."""
        with self._get_connection() as conn:
            cur = conn.cursor()

            # Trouver l'ID du prêt en cours
            cur.execute("""
                SELECT id FROM emprunts
                WHERE code_livre = ? AND date_retour_effective IS NULL
                ORDER BY id ASC LIMIT 1;
            """, (code_livre.strip().upper(),))
            row = cur.fetchone()
            if not row:
                return False

            emprunt_id = row[0]
            cur.execute("""
                UPDATE emprunts
                SET date_retour_effective = ?
                WHERE id = ?;
            """, (date_retour_effective, emprunt_id))

            # Rendre le livre à nouveau disponible
            cur.execute("UPDATE livres SET disponible = 1 WHERE code = ?;", (code_livre.strip().upper(),))
            conn.commit()
            return True

    def lister_emprunts_en_cours(self) -> List[Emprunt]:
        """Retourne tous les emprunts non encore restitués."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code_livre, matricule, date_emprunt, date_retour_prevue, date_retour_effective
                FROM emprunts
                WHERE date_retour_effective IS NULL
                ORDER BY date_retour_prevue ASC;
            """)
            rows = cur.fetchall()
            return [
                Emprunt(
                    id_emprunt=r["id"],
                    code_livre=r["code_livre"],
                    matricule=r["matricule"],
                    date_emprunt=r["date_emprunt"],
                    date_retour_prevue=r["date_retour_prevue"],
                    date_retour_effective=r["date_retour_effective"]
                )
                for r in rows
            ]

    def lister_emprunts_par_lecteur(self, matricule: str, en_cours_uniquement: bool = True) -> List[Emprunt]:
        """Retourne les emprunts associés à un matricule étudiant."""
        mat = matricule.strip().upper()
        sql = "SELECT id, code_livre, matricule, date_emprunt, date_retour_prevue, date_retour_effective FROM emprunts WHERE matricule = ?"
        if en_cours_uniquement:
            sql += " AND date_retour_effective IS NULL"
        sql += " ORDER BY id DESC;"

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (mat,))
            rows = cur.fetchall()
            return [
                Emprunt(
                    id_emprunt=r["id"],
                    code_livre=r["code_livre"],
                    matricule=r["matricule"],
                    date_emprunt=r["date_emprunt"],
                    date_retour_prevue=r["date_retour_prevue"],
                    date_retour_effective=r["date_retour_effective"]
                )
                for r in rows
            ]

    def a_historique_emprunts_livre(self, code_livre: str) -> bool:
        """Vérifie si un livre a déjà été emprunté (règle d'intégrité)."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM emprunts WHERE code_livre = ?;", (code_livre.strip().upper(),))
            return cur.fetchone()[0] > 0

    def a_historique_emprunts_lecteur(self, matricule: str) -> bool:
        """Vérifie si un lecteur a déjà un historique de prêt (règle d'intégrité)."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM emprunts WHERE matricule = ?;", (matricule.strip().upper(),))
            return cur.fetchone()[0] > 0

    def lister_tous_les_emprunts(self) -> List[Emprunt]:
        """Retourne l'ensemble de l'historique de tous les emprunts."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code_livre, matricule, date_emprunt, date_retour_prevue, date_retour_effective
                FROM emprunts
                ORDER BY id DESC;
            """)
            rows = cur.fetchall()
            return [
                Emprunt(
                    id_emprunt=r["id"],
                    code_livre=r["code_livre"],
                    matricule=r["matricule"],
                    date_emprunt=r["date_emprunt"],
                    date_retour_prevue=r["date_retour_prevue"],
                    date_retour_effective=r["date_retour_effective"]
                )
                for r in rows
            ]

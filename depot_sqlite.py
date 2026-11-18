"""
Module depot_sqlite.py - Couche d'accès aux données (persistance SQLite) pour BiblioIIT.
Gère la création des tables, le stockage des livres et des emprunts.
"""

import sqlite3
from typing import List, Optional
from modeles import Livre, Emprunt

DB_NAME = "biblio.db"

# Livres de référence de la bibliothèque (fonds de littérature africaine)
LIVRES_INITIAUX = [
    ("L001", "Climbié", "Bernard Dadié", 1956),
    ("L002", "Les Soleils des indépendances", "Ahmadou Kourouma", 1968),
    ("L003", "L'Aventure ambiguë", "Cheikh Hamidou Kane", 1961),
    ("L004", "Allah n'est pas obligé", "Ahmadou Kourouma", 2000),
    ("L005", "Le monde s'effondre", "Chinua Achebe", 1958),
    ("L006", "Une si longue lettre", "Mariama Bâ", 1979),
    ("L007", "L'Enfant noir", "Camara Laye", 1953),
    ("L008", "L'Étrange Destin de Wangrin", "Amadou Hampâté Bâ", 1973),
    ("L009", "Sous l'orage", "Seydou Badian", 1957),
    ("L010", "Rebelle", "Fatou Keïta", 1998),
    ("L011", "Les Frasques d'Ébinto", "Amadou Koné", 1975),
    ("L012", "Le Pagne noir", "Bernard Dadié", 1955),
    ("L013", "Un Nègre à Paris", "Bernard Dadié", 1959),
    ("L014", "Le Pauvre Christ de Bomba", "Mongo Beti", 1956),
    ("L015", "Ville cruelle", "Eza Boto", 1954),
    ("L016", "Cahier d'un retour au pays natal", "Aimé Césaire", 1939),
    ("L017", "Batouala", "René Maran", 1921),
    ("L018", "La Rue Cases-Nègres", "Joseph Zobel", 1950),
    ("L019", "Cœur de caniche", "Isaïe Biton Koulibaly", 1989),
    ("L020", "Ah ! Les femmes...", "Isaïe Biton Koulibaly", 1999),
    ("L021", "Le Baobab fou", "Ken Bugul", 1982),
    ("L022", "Les Crapauds-broussards", "Tierno Monénembo", 1979),
    ("L023", "Verre Cassé", "Alain Mabanckou", 2005),
    ("L024", "Petit Pays", "Gaël Faye", 2016),
    ("L025", "La Plus Secrète Mémoire des hommes", "Mohamed Mbougar Sarr", 2021),
]


class DepotSqlite:
    """Gère toutes les interactions directes avec la base SQLite."""

    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self._initialiser_base()

    def _get_connection(self) -> sqlite3.Connection:
        """Ouvre une connexion avec activation des clés étrangères."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _initialiser_base(self):
        """Crée les tables nécessaires et insère le fonds initial de livres."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS livres (
                    code TEXT PRIMARY KEY,
                    titre TEXT NOT NULL,
                    auteur TEXT NOT NULL,
                    annee INTEGER NOT NULL,
                    disponible INTEGER DEFAULT 1
                );
            """)

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

            # Insérer les livres initiaux du fonds documentaire (sans écraser les existants)
            cur.executemany(
                "INSERT OR IGNORE INTO livres (code, titre, auteur, annee, disponible) VALUES (?, ?, ?, ?, 1);",
                LIVRES_INITIAUX
            )
            conn.commit()

    def rechercher_livres(self, mot_cle: str) -> List[Livre]:
        """
        Recherche des livres par mot-clé dans le titre ou l'auteur.
        Insensible à la casse.
        """
        pattern = f"%{mot_cle.strip().lower()}%"
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT code, titre, auteur, annee, disponible
                FROM livres
                WHERE LOWER(titre) LIKE ? OR LOWER(auteur) LIKE ?
                ORDER BY code ASC;
            """, (pattern, pattern))
            rows = cur.fetchall()
            return [
                Livre(
                    code=r["code"],
                    titre=r["titre"],
                    auteur=r["auteur"],
                    annee=r["annee"],
                    disponible=bool(r["disponible"])
                )
                for r in rows
            ]

    def obtenir_livre(self, code_livre: str) -> Optional[Livre]:
        """Récupère un livre par son code unique (ex: 'L002')."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT code, titre, auteur, annee, disponible
                FROM livres
                WHERE code = ?;
            """, (code_livre.strip(),))
            row = cur.fetchone()
            if row:
                return Livre(
                    code=row["code"],
                    titre=row["titre"],
                    auteur=row["auteur"],
                    annee=row["annee"],
                    disponible=bool(row["disponible"])
                )
            return None

    def enregistrer_emprunt(self, emprunt: Emprunt) -> Emprunt:
        """Sauvegarde un emprunt et marque le livre comme indisponible."""
        with self._get_connection() as conn:
            cur = conn.cursor()
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

            # Mettre le livre à indisponible
            cur.execute("UPDATE livres SET disponible = 0 WHERE code = ?;", (emprunt.code_livre,))
            conn.commit()
            return emprunt

    def enregistrer_retour(self, code_livre: str, date_retour_effective: str) -> bool:
        """
        Clôture l'emprunt actif d'un livre et le rend à nouveau disponible.
        Retourne True si un emprunt a été clôturé, False sinon.
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            # Mettre à jour l'emprunt en cours (date_retour_effective est NULL)
            cur.execute("""
                UPDATE emprunts
                SET date_retour_effective = ?
                WHERE code_livre = ? AND date_retour_effective IS NULL;
            """, (date_retour_effective, code_livre.strip()))

            modifie = cur.rowcount > 0
            if modifie:
                # Rendre le livre à nouveau disponible
                cur.execute("UPDATE livres SET disponible = 1 WHERE code = ?;", (code_livre.strip(),))
            conn.commit()
            return modifie

    def lister_emprunts_en_cours(self) -> List[Emprunt]:
        """Retourne la liste de tous les emprunts non encore restitués."""
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

    def lister_tous_les_livres(self) -> List[Livre]:
        """Retourne la totalité des ouvrages du catalogue."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT code, titre, auteur, annee, disponible FROM livres ORDER BY code ASC;")
            rows = cur.fetchall()
            return [
                Livre(
                    code=r["code"],
                    titre=r["titre"],
                    auteur=r["auteur"],
                    annee=r["annee"],
                    disponible=bool(r["disponible"])
                )
                for r in rows
            ]

"""
Module modeles.py - Définition des structures de données du projet BiblioIIT.
Contient les entités Livre et Emprunt.
"""

from datetime import date
from typing import Optional, Union


class Livre:
    """Représente un ouvrage présent dans le fonds de la bibliothèque."""

    def __init__(self, code: str, titre: str, auteur: str, annee: int, disponible: bool = True):
        self.code = str(code).strip()
        self.titre = str(titre).strip()
        self.auteur = str(auteur).strip()
        self.annee = int(annee)
        self.disponible = bool(disponible)

    def __str__(self) -> str:
        # Format d'affichage identique à la console du professeur
        # Ex : L004  Allah n'est pas obligé - Ahmadou Kourouma (2000)
        return f"{self.code}  {self.titre} - {self.auteur} ({self.annee})"

    def __repr__(self) -> str:
        return f"Livre(code='{self.code}', titre='{self.titre}', auteur='{self.auteur}', annee={self.annee})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Livre):
            return self.code == other.code
        return False


class Emprunt:
    """Représente l'emprunt d'un livre par un étudiant."""

    def __init__(
        self,
        code_livre: str,
        matricule: str,
        date_emprunt: Union[date, str],
        date_retour_prevue: Union[date, str],
        date_retour_effective: Optional[Union[date, str]] = None,
        id_emprunt: Optional[int] = None
    ):
        self.id = id_emprunt
        self.code_livre = str(code_livre).strip()
        self.matricule = str(matricule).strip()
        self.date_emprunt = str(date_emprunt)
        self.date_retour_prevue = str(date_retour_prevue)
        self.date_retour_effective = str(date_retour_effective) if date_retour_effective else None

    def est_en_cours(self) -> bool:
        """Indique si l'emprunt est toujours actif (livre non encore rendu)."""
        return self.date_retour_effective is None

    def __repr__(self) -> str:
        return (
            f"Emprunt(id={self.id}, code_livre='{self.code_livre}', "
            f"matricule='{self.matricule}', retour_prevu='{self.date_retour_prevue}')"
        )

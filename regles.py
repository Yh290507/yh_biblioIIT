"""
Module regles.py - Règles métier et de gestion pour la bibliothèque BiblioIIT.
Définit les durées d'emprunt, la détection des retards et les validations de disponibilité.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Union, List
from modeles import Livre, Emprunt

# Durée standard d'un emprunt en jours
DUREE_EMPRUNT_JOURS: int = 14


class BiblioErreur(Exception):
    """Exception de base pour les erreurs métier de la bibliothèque."""
    pass


class LivreDejaEmprunteError(BiblioErreur):
    """Levée lorsqu'on tente d'emprunter un livre déjà emprunté."""
    def __init__(self, titre_livre: str):
        super().__init__(f"Impossible : Le livre « {titre_livre} » est déjà emprunté")
        self.titre_livre = titre_livre


class LivreIntrouvableError(BiblioErreur):
    """Levée lorsqu'un code de livre n'existe pas dans le catalogue."""
    def __init__(self, code_livre: str):
        super().__init__(f"Erreur : Aucun livre trouvé avec le code '{code_livre}'")
        self.code_livre = code_livre


class EmpruntIntrouvableError(BiblioErreur):
    """Levée lorsqu'aucun emprunt actif ne correspond au retour demandé."""
    def __init__(self, code_livre: str):
        super().__init__(f"Erreur : Aucun emprunt en cours pour le livre '{code_livre}'")
        self.code_livre = code_livre


def _parse_date(val: Union[date, str]) -> date:
    """Convertit une chaîne 'YYYY-MM-DD' ou un objet date en objet date."""
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except ValueError:
        # Essai avec le format DD/MM/YYYY
        return datetime.strptime(str(val).strip(), "%d/%m/%Y").date()


def calculer_date_retour(
    date_emprunt: Optional[Union[date, str]] = None,
    duree_jours: int = DUREE_EMPRUNT_JOURS
) -> date:
    """Calcule la date de retour prévue à partir de la date d'emprunt."""
    base_date = _parse_date(date_emprunt) if date_emprunt else date.today()
    return base_date + timedelta(days=duree_jours)


def est_en_retard(emprunt: Emprunt, date_reference: Optional[Union[date, str]] = None) -> bool:
    """
    Indique si un emprunt est en retard.
    Un emprunt est en retard s'il est toujours en cours et que la date prévue est dépassée.
    """
    if not emprunt.est_en_cours():
        return False

    ref_date = _parse_date(date_reference) if date_reference else date.today()
    date_prevue = _parse_date(emprunt.date_retour_prevue)
    return ref_date > date_prevue


def calculer_jours_retard(emprunt: Emprunt, date_reference: Optional[Union[date, str]] = None) -> int:
    """Calcule le nombre de jours de retard d'un emprunt en cours (0 si aucun retard)."""
    if not est_en_retard(emprunt, date_reference):
        return 0

    ref_date = _parse_date(date_reference) if date_reference else date.today()
    date_prevue = _parse_date(emprunt.date_retour_prevue)
    return (ref_date - date_prevue).days


def verifier_livre_disponible(livre: Livre, emprunts_actifs: List[Emprunt]) -> bool:
    """
    Vérifie si un livre peut être emprunté.
    Lève LivreDejaEmprunteError si le livre est déjà entre les mains d'un lecteur.
    """
    for emp in emprunts_actifs:
        if emp.code_livre == livre.code and emp.est_en_cours():
            raise LivreDejaEmprunteError(livre.titre)
    return True

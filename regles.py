"""
Module regles.py - Règles métier et de gestion pour la bibliothèque BiblioIIT.
Définit les durées d'emprunt, les quotas d'étudiants, les détections de retard
et les validations de disponibilité conformes aux pratiques réelles des bibliothèques.
"""

import json
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, Union, List, Dict, Any
from modeles import Livre, Lecteur, Emprunt

# Configuration par défaut
DUREE_EMPRUNT_JOURS: int = 14
MAX_EMPRUNTS_PAR_LECTEUR: int = 3
BLOQUER_SI_RETARD_ACTIF: bool = True


def charger_config(chemin_config: Optional[str] = None) -> Dict[str, Any]:
    """Charge la configuration depuis un fichier JSON ou retourne les valeurs par défaut."""
    global DUREE_EMPRUNT_JOURS, MAX_EMPRUNTS_PAR_LECTEUR, BLOQUER_SI_RETARD_ACTIF

    config_path = Path(chemin_config) if chemin_config else Path(__file__).resolve().parent / "config.json"
    config = {
        "duree_emprunt_jours": DUREE_EMPRUNT_JOURS,
        "max_livres_par_lecteur": MAX_EMPRUNTS_PAR_LECTEUR,
        "bloquer_si_retard_actif": BLOQUER_SI_RETARD_ACTIF,
        "nom_etablissement": "Institut Ivoirien de Technologie (IIT)"
    }

    if config_path.is_file():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                config.update(data)
                DUREE_EMPRUNT_JOURS = int(config.get("duree_emprunt_jours", 14))
                MAX_EMPRUNTS_PAR_LECTEUR = int(config.get("max_livres_par_lecteur", 3))
                BLOQUER_SI_RETARD_ACTIF = bool(config.get("bloquer_si_retard_actif", True))
        except Exception:
            pass

    return config


# Chargement initial au démarrage du module
charger_config()


class BiblioErreur(Exception):
    """Exception de base pour les erreurs métier de la bibliothèque."""
    pass


class LivreDejaEmprunteError(BiblioErreur):
    """Levée lorsqu'on tente d'emprunter un livre déjà emprunté (message exact du cours)."""
    def __init__(self, titre_livre: str):
        super().__init__(f"Impossible : Le livre « {titre_livre} » est déjà emprunté")
        self.titre_livre = titre_livre


class LivreIntrouvableError(BiblioErreur):
    """Levée lorsqu'un code de livre n'existe pas dans le catalogue."""
    def __init__(self, code_livre: str):
        super().__init__(f"Erreur : Aucun livre trouvé avec le code '{code_livre}'")
        self.code_livre = code_livre


class LecteurIntrouvableError(BiblioErreur):
    """Levée lorsqu'un matricule de lecteur n'est pas trouvé."""
    def __init__(self, matricule: str):
        super().__init__(f"Erreur : Aucun lecteur trouvé avec le matricule '{matricule}'")
        self.matricule = matricule


class EmpruntIntrouvableError(BiblioErreur):
    """Levée lorsqu'aucun emprunt actif ne correspond au retour demandé."""
    def __init__(self, code_livre: str):
        super().__init__(f"Erreur : Aucun emprunt en cours pour le livre '{code_livre}'")
        self.code_livre = code_livre


class QuotaEmpruntsDepasseError(BiblioErreur):
    """Levée lorsqu'un lecteur tente de dépasser le quota maximal d'emprunts simultanés."""
    def __init__(self, matricule: str, max_prets: int):
        super().__init__(
            f"Quota atteint : Le lecteur '{matricule}' a déjà {max_prets} livre(s) en cours d'emprunt."
        )
        self.matricule = matricule
        self.max_prets = max_prets


class LecteurAvecRetardBloqueError(BiblioErreur):
    """Levée lorsqu'un lecteur avec un retard actif tente d'emprunter un nouvel ouvrage."""
    def __init__(self, matricule: str, nb_retards: int):
        super().__init__(
            f"Prêt refusé : Le lecteur '{matricule}' a {nb_retards} livre(s) en retard non restitué(s)."
        )
        self.matricule = matricule
        self.nb_retards = nb_retards


class LivreDejaEnCoursParLecteurError(BiblioErreur):
    """Levée lorsqu'un lecteur tente d'emprunter un second exemplaire du même livre."""
    def __init__(self, titre_livre: str):
        super().__init__(
            f"Prêt refusé : L'étudiant a déjà un exemplaire de « {titre_livre} » en cours d'emprunt."
        )
        self.titre_livre = titre_livre


class SuppressionImpossibleError(BiblioErreur):
    """Levée lors d'une tentative de suppression d'un livre ou lecteur ayant un historique."""
    def __init__(self, entite: str, identifiant: str, motif: str):
        super().__init__(f"Suppression impossible de {entite} '{identifiant}' : {motif}")
        self.entite = entite
        self.identifiant = identifiant


def _parse_date(val: Union[date, str]) -> date:
    """Convertit une chaîne 'YYYY-MM-DD' ou un objet date en objet date."""
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except ValueError:
        return datetime.strptime(str(val).strip(), "%d/%m/%Y").date()


def calculer_date_retour(
    date_emprunt: Optional[Union[date, str]] = None,
    duree_jours: Optional[int] = None
) -> date:
    """Calcule la date de retour prévue à partir de la date d'emprunt."""
    duree = duree_jours if duree_jours is not None else DUREE_EMPRUNT_JOURS
    base_date = _parse_date(date_emprunt) if date_emprunt else date.today()
    return base_date + timedelta(days=duree)


def est_en_retard(emprunt: Emprunt, date_reference: Optional[Union[date, str]] = None) -> bool:
    """Indique si un emprunt en cours a dépassé son échéance."""
    if not emprunt.est_en_cours():
        return False

    ref_date = _parse_date(date_reference) if date_reference else date.today()
    date_prevue = _parse_date(emprunt.date_retour_prevue)
    return ref_date > date_prevue


def calculer_jours_retard(emprunt: Emprunt, date_reference: Optional[Union[date, str]] = None) -> int:
    """Calcule le nombre de jours de dépassement pour un emprunt en retard."""
    if not est_en_retard(emprunt, date_reference):
        return 0

    ref_date = _parse_date(date_reference) if date_reference else date.today()
    date_prevue = _parse_date(emprunt.date_retour_prevue)
    return (ref_date - date_prevue).days


def verifier_livre_disponible(livre: Livre, emprunts_actifs: List[Emprunt]) -> bool:
    """
    Vérifie si un livre a des exemplaires disponibles.
    Pour compatibilité avec le scénario du slide : lève LivreDejaEmprunteError
    dès que le nombre d'emprunts actifs atteint le nombre d'exemplaires du livre.
    """
    actifs_ce_livre = [emp for emp in emprunts_actifs if emp.code_livre == livre.code and emp.est_en_cours()]
    if len(actifs_ce_livre) >= livre.nb_exemplaires:
        raise LivreDejaEmprunteError(livre.titre)
    return True


def verifier_quota_lecteur(
    matricule: str,
    emprunts_actifs_lecteur: List[Emprunt],
    max_autorise: Optional[int] = None
) -> bool:
    """Vérifie que le lecteur n'a pas atteint le quota maximum de prêts simultanés."""
    limite = max_autorise if max_autorise is not None else MAX_EMPRUNTS_PAR_LECTEUR
    if len(emprunts_actifs_lecteur) >= limite:
        raise QuotaEmpruntsDepasseError(matricule, limite)
    return True


def verifier_lecteur_sans_retard(
    matricule: str,
    emprunts_actifs_lecteur: List[Emprunt],
    date_ref: Optional[Union[date, str]] = None
) -> bool:
    """Vérifie que l'usager n'a aucun prêt en retard non régularisé."""
    retards = [e for e in emprunts_actifs_lecteur if est_en_retard(e, date_ref)]
    if retards:
        raise LecteurAvecRetardBloqueError(matricule, len(retards))
    return True


def verifier_non_doublon_emprunt(livre: Livre, emprunts_actifs_lecteur: List[Emprunt]) -> bool:
    """Empêche un usager d'avoir simultanément deux exemplaires du même livre."""
    for emp in emprunts_actifs_lecteur:
        if emp.code_livre == livre.code and emp.est_en_cours():
            raise LivreDejaEnCoursParLecteurError(livre.titre)
    return True

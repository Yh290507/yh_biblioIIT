"""
Module service.py - Logique applicative et cas d'usage pour BiblioIIT.
Orchestre les opérations de la bibliothèque en combinant le dépôt de données
(depot_sqlite.py) et les règles métier (regles.py).
"""

from datetime import date
from typing import List, Dict, Any, Optional
from modeles import Livre, Emprunt
from depot_sqlite import DepotSqlite
from regles import (
    calculer_date_retour,
    est_en_retard,
    calculer_jours_retard,
    verifier_livre_disponible,
    LivreIntrouvableError,
    EmpruntIntrouvableError,
)


class BibliothequeService:
    """Service centralisant tous les cas d'usage de la bibliothèque BiblioIIT."""

    def __init__(self, depot: Optional[DepotSqlite] = None):
        # Injection de dépendance : permet d'utiliser le dépôt par défaut
        # ou un dépôt de test sans modifier le code du service
        self.depot = depot if depot is not None else DepotSqlite()

    def rechercher_livres(self, mot_cle: str) -> List[Livre]:
        """Recherche les livres dont le titre ou l'auteur contient le mot-clé."""
        if not mot_cle or not mot_cle.strip():
            return self.depot.lister_tous_les_livres()
        return self.depot.rechercher_livres(mot_cle)

    def obtenir_livre(self, code_livre: str) -> Livre:
        """Récupère un livre par son code ou lève une exception s'il n'existe pas."""
        livre = self.depot.obtenir_livre(code_livre)
        if not livre:
            raise LivreIntrouvableError(code_livre)
        return livre

    def emprunter_livre(
        self,
        code_livre: str,
        matricule: str,
        date_emprunt: Optional[str] = None
    ) -> Emprunt:
        """
        Enregistre l'emprunt d'un livre pour un étudiant.
        1. Vérifie l'existence du livre.
        2. Vérifie sa disponibilité via regles.py (lève LivreDejaEmprunteError si déjà sorti).
        3. Calcule la date de retour prévue (J + 14).
        4. Enregistre dans la base SQLite.
        """
        livre = self.obtenir_livre(code_livre)

        # Vérification des emprunts en cours
        emprunts_actifs = self.depot.lister_emprunts_en_cours()
        verifier_livre_disponible(livre, emprunts_actifs)

        # Calcul de la date de retour prévue
        d_emprunt = date_emprunt if date_emprunt else str(date.today())
        d_prevue = str(calculer_date_retour(d_emprunt))

        emprunt = Emprunt(
            code_livre=livre.code,
            matricule=matricule,
            date_emprunt=d_emprunt,
            date_retour_prevue=d_prevue
        )
        return self.depot.enregistrer_emprunt(emprunt)

    def rendre_livre(
        self,
        code_livre: str,
        date_retour_effective: Optional[str] = None
    ) -> bool:
        """
        Enregistre la restitution d'un livre emprunté.
        Lève EmpruntIntrouvableError si aucun emprunt n'était en cours pour ce livre.
        """
        # Vérifie d'abord que le livre existe dans le catalogue
        self.obtenir_livre(code_livre)

        d_effective = date_retour_effective if date_retour_effective else str(date.today())
        succes = self.depot.enregistrer_retour(code_livre, d_effective)
        if not succes:
            raise EmpruntIntrouvableError(code_livre)
        return True

    def lister_retards(self, date_reference: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retourne la liste des emprunts actuellement en retard avec le livre associé
        et le nombre de jours de dépassement.
        """
        emprunts_actifs = self.depot.lister_emprunts_en_cours()
        retards = []

        for emp in emprunts_actifs:
            if est_en_retard(emp, date_reference):
                livre = self.depot.obtenir_livre(emp.code_livre)
                jours = calculer_jours_retard(emp, date_reference)
                retards.append({
                    "emprunt": emp,
                    "livre": livre,
                    "jours_retard": jours
                })

        return retards

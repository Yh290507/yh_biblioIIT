"""
Module service.py - Logique applicative et cas d'usage pour BiblioIIT.
Orchestre les opérations de la bibliothèque (livres, lecteurs, prêts, statistiques)
en combinant le dépôt de données (depot_sqlite.py) et les règles métier (regles.py).
"""

import csv
from datetime import date
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from modeles import Livre, Lecteur, Emprunt
from depot_sqlite import DepotSqlite
from regles import (
    charger_config,
    calculer_date_retour,
    est_en_retard,
    calculer_jours_retard,
    verifier_livre_disponible,
    verifier_quota_lecteur,
    verifier_lecteur_sans_retard,
    verifier_non_doublon_emprunt,
    LivreIntrouvableError,
    LecteurIntrouvableError,
    EmpruntIntrouvableError,
    SuppressionImpossibleError,
)


class BibliothequeService:
    """Service centralisant tous les cas d'usage de la bibliothèque BiblioIIT."""

    def __init__(self, depot: Optional[DepotSqlite] = None, config_path: Optional[str] = None):
        # Injection de dépendance pour persistance et configuration
        self.depot = depot if depot is not None else DepotSqlite()
        self.config = charger_config(config_path)

    # ==========================================================
    # CAS D'USAGE : CATALOGUE DES LIVRES
    # ==========================================================

    def rechercher_livres(self, mot_cle: str = "") -> List[Livre]:
        """Recherche les livres par titre, auteur ou catégorie (ou tous si vide)."""
        if not mot_cle or not mot_cle.strip():
            return self.depot.lister_tous_les_livres()
        return self.depot.rechercher_livres(mot_cle)

    def obtenir_livre(self, code_livre: str) -> Livre:
        """Récupère un livre par son code ou lève LivreIntrouvableError."""
        livre = self.depot.obtenir_livre(code_livre)
        if not livre:
            raise LivreIntrouvableError(code_livre)
        return livre

    def ajouter_livre(
        self,
        code: str,
        titre: str,
        auteur: str,
        annee: int,
        categorie: str = "Littérature africaine",
        nb_exemplaires: int = 1
    ) -> Livre:
        """Ajoute un nouvel ouvrage au fonds documentaire."""
        nouveau_livre = Livre(
            code=code,
            titre=titre,
            auteur=auteur,
            annee=annee,
            categorie=categorie,
            nb_exemplaires=nb_exemplaires
        )
        return self.depot.ajouter_livre(nouveau_livre)

    def supprimer_livre(self, code_livre: str) -> bool:
        """
        Supprime un livre du catalogue.
        Lève SuppressionImpossibleError si le livre a un historique de prêt.
        """
        livre = self.obtenir_livre(code_livre)
        if self.depot.a_historique_emprunts_livre(livre.code):
            raise SuppressionImpossibleError(
                "du livre",
                livre.code,
                f"L'ouvrage « {livre.titre} » possède un historique de prêt et ne peut être supprimé."
            )
        return self.depot.supprimer_livre(livre.code)

    # ==========================================================
    # CAS D'USAGE : LECTEURS (USAGERS / ÉTUDIANTS)
    # ==========================================================

    def inscrire_lecteur(
        self,
        matricule: str,
        nom: str,
        prenom: str,
        contact: str = "",
        filiere: str = "Génie Logiciel"
    ) -> Lecteur:
        """Inscrit un nouvel étudiant comme lecteur de la bibliothèque."""
        lecteur = Lecteur(matricule=matricule, nom=nom, prenom=prenom, contact=contact, filiere=filiere)
        return self.depot.ajouter_lecteur(lecteur)

    def obtenir_lecteur(self, matricule: str) -> Lecteur:
        """Récupère un lecteur par son matricule ou lève LecteurIntrouvableError."""
        lecteur = self.depot.obtenir_lecteur(matricule)
        if not lecteur:
            raise LecteurIntrouvableError(matricule)
        return lecteur

    def lister_lecteurs(self) -> List[Lecteur]:
        """Retourne la liste de tous les lecteurs enregistrés."""
        return self.depot.lister_lecteurs()

    def rechercher_lecteurs(self, mot_cle: str) -> List[Lecteur]:
        """Recherche des lecteurs par matricule, nom, prénom ou filière."""
        if not mot_cle or not mot_cle.strip():
            return self.depot.lister_lecteurs()
        return self.depot.rechercher_lecteurs(mot_cle)

    def supprimer_lecteur(self, matricule: str) -> bool:
        """
        Supprime un lecteur de la base.
        Lève SuppressionImpossibleError s'il possède un historique de prêt.
        """
        lecteur = self.obtenir_lecteur(matricule)
        if self.depot.a_historique_emprunts_lecteur(lecteur.matricule):
            raise SuppressionImpossibleError(
                "du lecteur",
                lecteur.matricule,
                f"L'étudiant « {lecteur.nom_complet} » possède un historique d'emprunt et ne peut être supprimé."
            )
        return self.depot.supprimer_lecteur(lecteur.matricule)

    # ==========================================================
    # CAS D'USAGE : EMPRUNTS ET RESTITUTIONS
    # ==========================================================

    def emprunter_livre(
        self,
        code_livre: str,
        matricule: str,
        date_emprunt: Optional[str] = None
    ) -> Emprunt:
        """
        Enregistre l'emprunt d'un livre en appliquant toutes les règles métier :
        1. Vérifie l'existence du livre.
        2. Vérifie la disponibilité des exemplaires (lève LivreDejaEmprunteError si épuisé).
        3. Récupère les emprunts actifs de l'étudiant :
           - Vérifie le non-doublon d'emprunt du même titre.
           - Vérifie le quota maximal d'emprunts simultanés (ex: 3 max).
           - Vérifie l'absence de retards non régularisés (si activé dans config).
        4. Calcule l'échéance à J + 14 (paramétrable dans config.json).
        5. Enregistre dans la base SQLite.
        """
        livre = self.obtenir_livre(code_livre)
        mat = matricule.strip().upper()
        d_emprunt = date_emprunt if date_emprunt else str(date.today())

        # 1. Vérification de disponibilité des exemplaires
        emprunts_actifs = self.depot.lister_emprunts_en_cours()
        verifier_livre_disponible(livre, emprunts_actifs)

        # 2. Vérification des règles sur le lecteur
        emprunts_lecteur = self.depot.lister_emprunts_par_lecteur(mat, en_cours_uniquement=True)

        # Pas de doublon : l'étudiant ne peut pas avoir 2 fois le même livre en même temps
        verifier_non_doublon_emprunt(livre, emprunts_lecteur)

        # Quota maximal de prêts
        max_prets = self.config.get("max_livres_par_lecteur", 3)
        verifier_quota_lecteur(mat, emprunts_lecteur, max_autorise=max_prets)

        # Règle de blocage si retard actif
        if self.config.get("bloquer_si_retard_actif", True):
            verifier_lecteur_sans_retard(mat, emprunts_lecteur, date_ref=d_emprunt)

        # 3. Calcul de la date de retour prévue
        duree = self.config.get("duree_emprunt_jours", 14)
        d_prevue = str(calculer_date_retour(d_emprunt, duree_jours=duree))

        emprunt = Emprunt(
            code_livre=livre.code,
            matricule=mat,
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
        Retourne True en cas de succès.
        Lève EmpruntIntrouvableError si aucun emprunt n'était en cours pour ce livre.
        """
        succes, _ = self.rendre_livre_avec_details(code_livre, date_retour_effective)
        return succes

    def rendre_livre_avec_details(
        self,
        code_livre: str,
        date_retour_effective: Optional[str] = None
    ) -> Tuple[bool, int]:
        """
        Enregistre la restitution et retourne (Succès, Jours_de_retard).
        Permet d'afficher un avertissement immédiat en cas de retour tardif.
        """
        # Vérifie l'existence du livre
        self.obtenir_livre(code_livre)

        d_effective = date_retour_effective if date_retour_effective else str(date.today())

        # Trouver l'emprunt en cours pour calculer un éventuel retard au retour
        emprunts = self.depot.lister_emprunts_en_cours()
        emprunt_cible = next((e for e in emprunts if e.code_livre == code_livre.strip().upper()), None)

        if not emprunt_cible:
            raise EmpruntIntrouvableError(code_livre)

        jours_retard = calculer_jours_retard(emprunt_cible, date_reference=d_effective)
        succes = self.depot.enregistrer_retour(code_livre, d_effective)
        return succes, jours_retard

    def lister_retards(self, date_reference: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retourne la liste des emprunts actuellement en retard avec le livre,
        le lecteur associé et le décompte des jours.
        """
        emprunts_actifs = self.depot.lister_emprunts_en_cours()
        retards = []

        for emp in emprunts_actifs:
            if est_en_retard(emp, date_reference):
                livre = self.depot.obtenir_livre(emp.code_livre)
                lecteur = self.depot.obtenir_lecteur(emp.matricule)
                jours = calculer_jours_retard(emp, date_reference)
                retards.append({
                    "emprunt": emp,
                    "livre": livre,
                    "lecteur": lecteur,
                    "jours_retard": jours
                })

        return retards

    # ==========================================================
    # CAS D'USAGE AVANCÉS : STATISTIQUES ET EXPORT (SIGB)
    # ==========================================================

    def obtenir_statistiques(self) -> Dict[str, Any]:
        """Calcule les indicateurs clés de performance (KPI) du fonds documentaire."""
        livres = self.depot.lister_tous_les_livres()
        emprunts_actifs = self.depot.lister_emprunts_en_cours()
        lecteurs = self.depot.lister_lecteurs()
        retards = self.lister_retards()

        total_exemplaires = sum(l.nb_exemplaires for l in livres)
        exemplaires_sortis = len(emprunts_actifs)
        exemplaires_dispos = max(0, total_exemplaires - exemplaires_sortis)

        taux_occupation = (
            round((exemplaires_sortis / total_exemplaires) * 100, 1)
            if total_exemplaires > 0
            else 0.0
        )

        return {
            "nb_titres": len(livres),
            "nb_exemplaires_total": total_exemplaires,
            "nb_exemplaires_dispos": exemplaires_dispos,
            "nb_emprunts_en_cours": exemplaires_sortis,
            "nb_retards": len(retards),
            "nb_lecteurs": len(lecteurs),
            "taux_occupation": taux_occupation,
        }

    def exporter_retards_csv(self, chemin_fichier: Optional[str] = None) -> str:
        """Exporte la liste des emprunts en retard dans un fichier CSV exploitable."""
        fichier = chemin_fichier if chemin_fichier else "rapport_retards.csv"
        retards = self.lister_retards()

        with open(fichier, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                "Code Livre",
                "Titre du Livre",
                "Auteur",
                "Matricule Étudiant",
                "Nom et Prénom",
                "Filière",
                "Contact",
                "Date Emprunt",
                "Date Limite",
                "Jours de Retard"
            ])

            for item in retards:
                emp: Emprunt = item["emprunt"]
                livre: Optional[Livre] = item["livre"]
                lecteur: Optional[Lecteur] = item["lecteur"]
                jours: int = item["jours_retard"]

                writer.writerow([
                    emp.code_livre,
                    livre.titre if livre else "",
                    livre.auteur if livre else "",
                    emp.matricule,
                    lecteur.nom_complet if lecteur else emp.matricule,
                    lecteur.filiere if lecteur else "",
                    lecteur.contact if lecteur else "",
                    emp.date_emprunt,
                    emp.date_retour_prevue,
                    jours
                ])

        return str(Path(fichier).resolve())

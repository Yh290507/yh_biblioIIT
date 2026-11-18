"""
Module console.py - Interface utilisateur en ligne de commande pour BiblioIIT.
Permet la gestion interactive complète de la bibliothèque universitaire de l'IIT :
recherche, circulation (prêts/retours), lecteurs, statistiques et exportations.
"""

import sys
from datetime import datetime
from typing import Optional
from service import BibliothequeService
from regles import (
    BiblioErreur,
    LivreDejaEmprunteError,
    LivreIntrouvableError,
    LecteurIntrouvableError,
    EmpruntIntrouvableError,
    QuotaEmpruntsDepasseError,
    LecteurAvecRetardBloqueError,
    LivreDejaEnCoursParLecteurError,
    SuppressionImpossibleError,
)


def _formater_date(date_str: str) -> str:
    """Transforme une date 'YYYY-MM-DD' en format convivial 'DD/MM/YYYY'."""
    try:
        dt = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return str(date_str)


class ApplicationConsole:
    """Gère l'affichage du menu et les interactions avec l'utilisateur."""

    def __init__(self, service: Optional[BibliothequeService] = None):
        self.service = service if service is not None else BibliothequeService()

    def afficher_banniere(self):
        """Affiche l'en-tête principal de BiblioIIT."""
        print()
        print("┌──────────────────────────────────────────────────────────────┐")
        print("│        INSTITUT IVOIRIEN DE TECHNOLOGIE — BIBLIOIIT          │")
        print("│            Système de Gestion de la Bibliothèque             │")
        print("└──────────────────────────────────────────────────────────────┘")

    def afficher_menu(self):
        """Affiche le menu des actions disponibles."""
        print()
        print("┌── MENU PRINCIPAL ────────────────────────────────────────────┐")
        print("│  [1]  Rechercher un livre      [2]  Emprunter un ouvrage     │")
        print("│  [3]  Restituer un livre       [4]  Suivi des retards        │")
        print("│  [5]  Gestion des Lecteurs     [6]  Tableau de bord & Stats  │")
        print("│  [7]  Ajouter un ouvrage       [8]  Exporter retards (CSV)   │")
        print("│  [9]  Guide & Règlement        [0]  Quitter l'application    │")
        print("└──────────────────────────────────────────────────────────────┘")

    # ==========================================================
    # ACTION 1 : RECHERCHER UN LIVRE
    # ==========================================================
    def action_rechercher(self):
        """Option 1 : Recherche d'un livre par mot-clé."""
        print()
        print("──  RECHERCHE D'OUVRAGES DANS LE CATALOGUE ──────────────────")
        mot_cle = input(" Saisissez un titre, auteur ou mot-clé (Entrée pour tout afficher) : ").strip()

        livres = self.service.rechercher_livres(mot_cle)

        if not livres:
            print(f"\n Aucun ouvrage ne correspond à la recherche : '{mot_cle}'.")
            return

        print(f"\n {len(livres)} ouvrage(s) trouvé(s) :\n")
        print(f"  {'CODE':<6} {'STATUT':<14} {'TITRE':<36} {'CATÉGORIE':<22} {'AUTEUR (ANNÉE)'}")
        print("  " + "─" * 98)

        for l in livres:
            dispo_str = f"[{l.nb_disponibles}/{l.nb_exemplaires} DISPO]" if l.disponible else "[ÉPUISÉ]"
            print(f"  {l.code:<6} {dispo_str:<14} {l.titre:<36} {l.categorie:<22} {l.auteur} ({l.annee})")
        print("  " + "─" * 98)

    # ==========================================================
    # ACTION 2 : EMPRUNTER UN OUVRAGE
    # ==========================================================
    def action_emprunter(self):
        """Option 2 : Enregistrement d'un nouvel emprunt."""
        print()
        print("──  ENREGISTREMENT D'UN NOUVEL EMPRUNT ──────────────────────")
        code = input(" Référence du livre à emprunter (ex: L002) : ").strip().upper()
        if not code:
            print(" Saisie annulée : le code ne peut pas être vide.")
            return

        matricule = input(" Matricule étudiant de l'emprunteur (ex: E2026-001) : ").strip().upper()
        if not matricule:
            print(" Saisie annulée : le matricule est obligatoire.")
            return

        try:
            # Vérifier si l'étudiant est déjà inscrit pour affichage personnalisé
            lecteur_existant = self.service.depot.obtenir_lecteur(matricule)

            emprunt = self.service.emprunter_livre(code, matricule)
            date_fmt = _formater_date(emprunt.date_retour_prevue)
            livre = self.service.obtenir_livre(code)

            nom_affiche = (
                f"{lecteur_existant.nom_complet} ({lecteur_existant.filiere})"
                if lecteur_existant and lecteur_existant.nom != "Étudiant"
                else matricule
            )

            print()
            print("┌──────────────────────────────────────────────────────────────┐")
            print("│  EMPRUNT ENREGISTRÉ AVEC SUCCÈS                              │")
            print(f"│ • Ouvrage      : {livre.titre} ({livre.code})")
            print(f"│ • Emprunteur   : {nom_affiche}")
            print(f"│ • Retour prévu : {date_fmt} (délai : {self.service.config.get('duree_emprunt_jours', 14)} jours)")
            print("└──────────────────────────────────────────────────────────────┘")

        except (LivreDejaEmprunteError,
                LivreIntrouvableError,
                QuotaEmpruntsDepasseError,
                LecteurAvecRetardBloqueError,
                LivreDejaEnCoursParLecteurError) as e:
            print(f"\n {e}")

    # ==========================================================
    # ACTION 3 : RESTITUTION D'UN OUVRAGE
    # ==========================================================
    def action_rendre(self):
        """Option 3 : Restitution d'un livre emprunté avec gestion du retard."""
        print()
        print("──   RESTITUTION D'UN OUVRAGE ───────────────────────────────")
        code = input(" Référence du livre à restituer (ex: L002) : ").strip().upper()
        if not code:
            print(" Saisie annulée.")
            return

        try:
            livre = self.service.obtenir_livre(code)
            succes, jours_retard = self.service.rendre_livre_avec_details(code)

            print(f"\n Le livre « {livre.titre} » ({livre.code}) a été restitué avec succès.")
            print(f"  Exemplaire réintégré en rayon. ({livre.nb_disponibles + 1}/{livre.nb_exemplaires} dispo)")

            if jours_retard > 0:
                print(f"\n  AVERTISSEMENT : Restitution tardive constatée ({jours_retard} jour(s) de retard) !")
                print("  Situation de l'étudiant désormais régularisée dans le système.")
            else:
                print("  Restitution effectuée dans les délais réglementaires.")

        except EmpruntIntrouvableError:
            print(f"\n  Le livre '{code}' n'est actuellement pas marqué comme emprunté.")
        except LivreIntrouvableError as e:
            print(f"\n {e}")

    # ==========================================================
    # ACTION 4 : SUIVI DES RETARDS
    # ==========================================================
    def action_retards(self):
        """Option 4 : Liste des emprunts en retard."""
        print()
        print("──   SUIVI DES EMPRUNTS EN RETARD ────────────────────────────")
        retards = self.service.lister_retards()

        if not retards:
            print("\n Aucun retard à signaler ! Tous les emprunts en cours sont dans les délais.")
            return

        print(f"\n  {len(retards)} emprunt(s) en dépassement de date limite :\n")
        for item in retards:
            emp = item["emprunt"]
            livre = item["livre"]
            lecteur = item["lecteur"]
            jours = item["jours_retard"]
            date_prevue_fmt = _formater_date(emp.date_retour_prevue)

            titre = livre.titre if livre else emp.code_livre
            nom_lecteur = f"{lecteur.nom_complet} ({lecteur.filiere})" if lecteur else emp.matricule
            contact = f" | Contact : {lecteur.contact}" if lecteur and lecteur.contact else ""

            print(f"  • [{emp.code_livre}] {titre}")
            print(f"    Emprunteur : {nom_lecteur}{contact}")
            print(f"    Date limite : {date_prevue_fmt}  ──  Retard constaté : {jours} jour(s)\n")

    # ==========================================================
    # ACTION 5 : GESTION DES LECTEURS (USAGERS)
    # ==========================================================
    def action_lecteurs(self):
        """Option 5 : Menu de gestion des étudiants/lecteurs."""
        print()
        print("──   GESTION DU FICHIER DES LECTEURS (ÉTUDIANTS) ─────────────")
        print(" [1] Inscrire un nouvel étudiant")
        print(" [2] Lister tous les lecteurs inscrits")
        print(" [3] Rechercher un lecteur")
        print(" [4] Supprimer une fiche lecteur")
        print(" [0] Retour au menu principal")

        sous_choix = input("\n Votre choix : ").strip()

        if sous_choix == "1":
            print("\n Inscription d'un nouvel usager :")
            mat = input(" Matricule (ex: E2026-050) : ").strip().upper()
            if not mat:
                print(" Matricule obligatoire."); return
            nom = input(" Nom de famille : ").strip().upper()
            prenom = input(" Prénom(s) : ").strip().title()
            fil = input(" Filière (ex: Génie Logiciel) : ").strip()
            tel = input(" Numéro de téléphone : ").strip()

            try:
                lecteur = self.service.inscrire_lecteur(mat, nom, prenom, tel, fil)
                print(f"\n Lecteur inscrit avec succès : {lecteur}")
            except Exception as e:
                print(f"\n Erreur lors de l'inscription : {e}")

        elif sous_choix == "2":
            lecteurs = self.service.lister_lecteurs()
            print(f"\n {len(lecteurs)} lecteur(s) inscrit(s) :\n")
            print(f"  {'MATRICULE':<12} {'NOM ET PRÉNOM':<28} {'FILIÈRE':<22} {'CONTACT'}")
            print("  " + "─" * 75)
            for lec in lecteurs:
                print(f"  {lec.matricule:<12} {lec.nom_complet:<28} {lec.filiere:<22} {lec.contact}")
            print("  " + "─" * 75)

        elif sous_choix == "3":
            mot = input("\n Rechercher un lecteur (Nom, Matricule ou Filière) : ").strip()
            resultats = self.service.rechercher_lecteurs(mot)
            if not resultats:
                print(f"\n Aucun lecteur trouvé pour '{mot}'.")
            else:
                print(f"\n {len(resultats)} résultat(s) :\n")
                for r in resultats:
                    print(f"  • [{r.matricule}] {r.nom_complet} — {r.filiere} ({r.contact})")

        elif sous_choix == "4":
            mat = input("\n Matricule du lecteur à supprimer : ").strip().upper()
            try:
                self.service.supprimer_lecteur(mat)
                print(f"\n La fiche de l'usager '{mat}' a été supprimée avec succès.")
            except (LecteurIntrouvableError, SuppressionImpossibleError) as e:
                print(f"\n {e}")

    # ==========================================================
    # ACTION 6 : TABLEAU DE BORD & STATISTIQUES (SIGB)
    # ==========================================================
    def action_statistiques(self):
        """Option 6 : Affiche les métriques et indicateurs du fonds documentaire."""
        print()
        print("──   TABLEAU DE BORD DU FONDS DOCUMENTAIRE (SIGB) ───────────")
        stats = self.service.obtenir_statistiques()

        print("┌──────────────────────────────────────────────────────────────┐")
        print(f"│ Établissement     : {self.service.config.get('nom_etablissement', 'IIT')}")
        print(f"│ Ouvrages (titres) : {stats['nb_titres']} titres répertoriés")
        print(f"│ Exemplaires total : {stats['nb_exemplaires_total']} exemplaires physiques")
        print(f"│ En rayon (dispos) : {stats['nb_exemplaires_dispos']} disponibles")
        print(f"│ Prêts en cours    : {stats['nb_emprunts_en_cours']} livre(s) actuellement sorti(s)")
        print(f"│ Retards déclarés  : {stats['nb_retards']} emprunt(s) en dépassement")
        print(f"│ Usagers inscrits  : {stats['nb_lecteurs']} étudiants actifs")
        print(f"│ Taux de rotation  : {stats['taux_occupation']} % du fonds emprunté")
        print("└──────────────────────────────────────────────────────────────┘")

    # ==========================================================
    # ACTION 7 : AJOUTER UN OUVRAGE
    # ==========================================================
    def action_ajouter_livre(self):
        """Option 7 : Ajout d'un livre au catalogue par le bibliothécaire."""
        print()
        print("──   ACQUISITION D'UN NOUVEL OUVRAGE DANS LE FONDS ──────────")
        code = input(" Code unique de l'ouvrage (ex: L026) : ").strip().upper()
        if not code:
            print(" Code obligatoire."); return
        titre = input(" Titre de l'ouvrage : ").strip()
        auteur = input(" Auteur : ").strip()
        try:
            annee = int(input(" Année de parution : ").strip())
        except ValueError:
            print(" Année invalide."); return
        cat = input(" Catégorie (ex: Roman, Théâtre, Essai, Poésie) : ").strip()
        try:
            ex = int(input(" Nombre d'exemplaires acquis (ex: 2) : ").strip() or "1")
        except ValueError:
            ex = 1

        try:
            livre = self.service.ajouter_livre(
                code=code,
                titre=titre,
                auteur=auteur,
                annee=annee,
                categorie=cat if cat else "Littérature",
                nb_exemplaires=ex
            )
            print(f"\n Ouvrage ajouté avec succès dans le fonds documentaire :")
            print(f"  {livre.code}  {livre.titre} - {livre.auteur} ({livre.annee}) [{livre.nb_exemplaires} ex.]")
        except Exception as e:
            print(f"\n Impossible d'ajouter le livre : {e}")

    # ==========================================================
    # ACTION 8 : EXPORTATION CSV DU RAPPORT DES RETARDS
    # ==========================================================
    def action_exporter_csv(self):
        """Option 8 : Exportation d'un fichier CSV pour l'administration."""
        print()
        print("──   EXPORTATION DU RAPPORT ADMINISTRATIF DES RETARDS ────────")
        nom_fichier = "rapport_retards_iit.csv"
        try:
            chemin = self.service.exporter_retards_csv(nom_fichier)
            print(f"\n Rapport exporté avec succès au format CSV :")
            print(f"  Chemin : {chemin}")
            print("  Fichier encodé en UTF-8 avec séparateurs point-virgule (compatible Excel).")
        except Exception as e:
            print(f"\n Erreur lors de l'exportation : {e}")

    # ==========================================================
    # ACTION 9 : GUIDE & RÈGLEMENT
    # ==========================================================
    def action_guide(self):
        """Option 9 : Affichage des règles de gestion de la bibliothèque."""
        print()
        print("──   RÈGLEMENT INTÉRIEUR & POLITIQUES DE PRÊT (BIBLIOIIT) ───")
        duree = self.service.config.get("duree_emprunt_jours", 14)
        max_livres = self.service.config.get("max_livres_par_lecteur", 3)
        bloq = "Oui (Blocage strict)" if self.service.config.get("bloquer_si_retard_actif", True) else "Non"

        print("┌──────────────────────────────────────────────────────────────┐")
        print(f"│ 1. Durée maximale du prêt      : {duree} jours calendaires")
        print(f"│ 2. Quota maximal simultané     : {max_livres} livres max par étudiant")
        print(f"│ 3. Prêt bloqué si retard actif : {bloq}")
        print(f"│ 4. Doublon d'emprunt           : Interdit (1 ex. d'un titre à la fois)")
        print(f"│ 5. Suppression de notice/fiche : Interdite si historique existant")
        print(f"│ 6. Configuration modifiable    : Fichier config.json à la racine")
        print("└──────────────────────────────────────────────────────────────┘")

    # ==========================================================
    # BOUCLE PRINCIPALE
    # ==========================================================
    def executer(self):
        """Boucle principale de l'application console."""
        self.afficher_banniere()

        actions = {
            "1": self.action_rechercher,
            "2": self.action_emprunter,
            "3": self.action_rendre,
            "4": self.action_retards,
            "5": self.action_lecteurs,
            "6": self.action_statistiques,
            "7": self.action_ajouter_livre,
            "8": self.action_exporter_csv,
            "9": self.action_guide,
        }

        while True:
            self.afficher_menu()
            choix = input("\n Votre choix : ").strip()

            if choix == "0":
                print("\n Merci d'avoir utilisé BiblioIIT. À bientôt !")
                break
            elif choix in actions:
                actions[choix]()
            else:
                print("\n  Choix invalide. Veuillez sélectionner une option entre 0 et 9.")


def main():
    """Point d'entrée du programme."""
    app = ApplicationConsole()
    try:
        app.executer()
    except (KeyboardInterrupt, EOFError):
        print("\n\nFermeture de l'application...")
        sys.exit(0)


if __name__ == "__main__":
    main()

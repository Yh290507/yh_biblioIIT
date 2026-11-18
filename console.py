"""
Module console.py - Interface utilisateur en ligne de commande pour BiblioIIT.
Permet la gestion interactive de la bibliothèque de l'Institut Ivoirien de Technologie.
"""

import sys
from datetime import datetime
from typing import Optional
from service import BibliothequeService
from regles import (
    LivreDejaEmprunteError,
    LivreIntrouvableError,
    EmpruntIntrouvableError,
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
        print("│  [3]   Restituer un livre       [4]   Suivi des retards      │")
        print("│  [0]  Quitter l'application                                  │")
        print("└──────────────────────────────────────────────────────────────┘")

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
        print(f"  {'CODE':<6} {'STATUT':<14} {'TITRE':<38} {'AUTEUR (ANNÉE)'}")
        print("  " + "─" * 78)

        for l in livres:
            statut = "[DISPONIBLE]" if l.disponible else "[EMPRUNTÉ]"
            print(f"  {l.code:<6} {statut:<14} {l.titre:<38} {l.auteur} ({l.annee})")
        print("  " + "─" * 78)

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
            emprunt = self.service.emprunter_livre(code, matricule)
            date_fmt = _formater_date(emprunt.date_retour_prevue)
            livre = self.service.obtenir_livre(code)

            print()
            print("┌──────────────────────────────────────────────────────────────┐")
            print("│  EMPRUNT ENREGISTRÉ AVEC SUCCÈS                              │")
            print(f"│ • Ouvrage      : {livre.titre} ({livre.code})")
            print(f"│ • Étudiant     : {matricule}")
            print(f"│ • Retour prévu : {date_fmt} (délai : 14 jours)")
            print("└──────────────────────────────────────────────────────────────┘")

        except LivreDejaEmprunteError as e:
            print(f"\n {e}")
        except LivreIntrouvableError as e:
            print(f"\n {e}")

    def action_rendre(self):
        """Option 3 : Restitution d'un livre emprunté."""
        print()
        print("──   RESTITUTION D'UN OUVRAGE ───────────────────────────────")
        code = input(" Référence du livre à restituer (ex: L002) : ").strip().upper()
        if not code:
            print(" Saisie annulée.")
            return

        try:
            livre = self.service.obtenir_livre(code)
            self.service.rendre_livre(code)
            print(f"\n Le livre « {livre.titre} » ({livre.code}) a été rendu avec succès.")
            print("  L'ouvrage est de nouveau disponible dans le catalogue.")

        except EmpruntIntrouvableError:
            print(f"\n  Le livre '{code}' n'est actuellement pas marqué comme emprunté.")
        except LivreIntrouvableError as e:
            print(f"\n {e}")

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
            jours = item["jours_retard"]
            date_prevue_fmt = _formater_date(emp.date_retour_prevue)

            titre = livre.titre if livre else emp.code_livre
            print(f"  • [{emp.code_livre}] {titre}")
            print(f"    Emprunteur : {emp.matricule} | Date limite : {date_prevue_fmt}")
            print(f"      Retard constaté : {jours} jour(s) de dépassement\n")

    def executer(self):
        """Boucle principale de l'application console."""
        self.afficher_banniere()

        while True:
            self.afficher_menu()
            choix = input("\n Votre choix : ").strip()

            if choix == "1":
                self.action_rechercher()
            elif choix == "2":
                self.action_emprunter()
            elif choix == "3":
                self.action_rendre()
            elif choix == "4":
                self.action_retards()
            elif choix == "0":
                print("\n Merci d'avoir utilisé BiblioIIT. À bientôt !")
                break
            else:
                print("\n  Choix invalide. Veuillez sélectionner une option entre 0 et 4.")


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

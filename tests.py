"""
Suite de tests unitaires pour le projet BiblioIIT.
Exécutable avec :
    python tests.py
ou avec :
    pytest
"""

from datetime import date
from modeles import Livre, Emprunt


def test_creation_livre():
    """Vérifie la création et l'affichage d'un livre."""
    livre = Livre("L004", "Allah n'est pas obligé", "Ahmadou Kourouma", 2000)
    assert livre.code == "L004"
    assert livre.titre == "Allah n'est pas obligé"
    assert livre.auteur == "Ahmadou Kourouma"
    assert livre.annee == 2000
    assert livre.disponible is True
    assert str(livre) == "L004  Allah n'est pas obligé - Ahmadou Kourouma (2000)"


def test_creation_emprunt():
    """Vérifie la création d'un emprunt en cours."""
    emprunt = Emprunt(
        code_livre="L002",
        matricule="E2026-001",
        date_emprunt=date(2026, 10, 1),
        date_retour_prevue=date(2026, 10, 15)
    )
    assert emprunt.code_livre == "L002"
    assert emprunt.matricule == "E2026-001"
    assert emprunt.est_en_cours() is True
    assert emprunt.date_retour_effective is None


def test_retour_emprunt():
    """Vérifie la clôture d'un emprunt."""
    emprunt = Emprunt(
        code_livre="L002",
        matricule="E2026-001",
        date_emprunt="2026-10-01",
        date_retour_prevue="2026-10-15",
        date_retour_effective="2026-10-14"
    )
    assert emprunt.est_en_cours() is False


if __name__ == "__main__":
    test_creation_livre()
    test_creation_emprunt()
    test_retour_emprunt()
    print("OK - Tous les tests de modeles.py ont réussi !")

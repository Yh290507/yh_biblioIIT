"""
Suite de tests unitaires pour le projet BiblioIIT.
Exécutable avec :
    python tests.py
ou avec :
    pytest
"""

from datetime import date, timedelta
from modeles import Livre, Emprunt
from regles import (
    calculer_date_retour,
    est_en_retard,
    calculer_jours_retard,
    verifier_livre_disponible,
    LivreDejaEmprunteError,
)


# ==========================================
# Tests des Modèles
# ==========================================

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


# ==========================================
# Tests des Règles Métier
# ==========================================

def test_calcul_date_retour():
    """Vérifie que la date de retour est bien à J + 14 par défaut."""
    d_emprunt = date(2026, 10, 1)
    d_retour = calculer_date_retour(d_emprunt, duree_jours=14)
    assert d_retour == date(2026, 10, 15)


def test_detection_retard():
    """Vérifie qu'un retard est correctement détecté."""
    emprunt = Emprunt(
        code_livre="L002",
        matricule="E2026-001",
        date_emprunt="2026-10-01",
        date_retour_prevue="2026-10-15"
    )
    # À la date limite : pas de retard
    assert est_en_retard(emprunt, date_reference="2026-10-15") is False
    assert calculer_jours_retard(emprunt, date_reference="2026-10-15") == 0

    # Lendemain : 1 jour de retard
    assert est_en_retard(emprunt, date_reference="2026-10-16") is True
    assert calculer_jours_retard(emprunt, date_reference="2026-10-16") == 1

    # 5 jours après : 5 jours de retard
    assert calculer_jours_retard(emprunt, date_reference="2026-10-20") == 5


def test_livre_deja_emprunte_leve_exception():
    """Vérifie qu'emprunter un livre déjà emprunté lève l'exception attendue."""
    livre = Livre("L002", "Les Soleils des indépendances", "Ahmadou Kourouma", 1968)
    emprunt_actif = Emprunt("L002", "E2026-001", "2026-10-01", "2026-10-15")

    try:
        verifier_livre_disponible(livre, [emprunt_actif])
        assert False, "Aurait dû lever LivreDejaEmprunteError"
    except LivreDejaEmprunteError as e:
        assert "Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté" in str(e)


if __name__ == "__main__":
    test_creation_livre()
    test_creation_emprunt()
    test_retour_emprunt()
    test_calcul_date_retour()
    test_detection_retard()
    test_livre_deja_emprunte_leve_exception()
    print("OK - Tous les tests de modeles.py et regles.py ont réussi !")

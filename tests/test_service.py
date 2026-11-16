"""
Tests unitaires et d'intégration pour service.py.
Valide le scénario complet présenté sur la diapositive du professeur :
1. Recherche par mot-clé (Kourouma)
2. Emprunt avec succès (L002 par E2026-001)
3. Blocage si réemprunt (L002 par E2026-002) avec le message exact
4. Retour du livre et restitution de sa disponibilité
5. Détection des retards
"""

import sys
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from depot_sqlite import DepotSqlite
from service import BibliothequeService
from regles import LivreDejaEmprunteError, LivreIntrouvableError, EmpruntIntrouvableError


def test_scenario_diaporama_complet():
    """Reproduit fidèlement la session console réelle du professeur."""
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = str(Path(temp_dir) / "test_service.db")
        depot = DepotSqlite(db_path=db_path)
        service = BibliothequeService(depot=depot)

        # 1. Recherche : Kourouma -> doit retourner L004 et L002
        resultats = service.rechercher_livres("Kourouma")
        assert len(resultats) == 2
        assert any(l.code == "L004" for l in resultats)
        assert any(l.code == "L002" for l in resultats)

        # 2. Emprunt : L002 par E2026-001 à la date 01/10/2026 -> retour prévu 15/10/2026
        emprunt = service.emprunter_livre(
            code_livre="L002",
            matricule="E2026-001",
            date_emprunt="2026-10-01"
        )
        assert emprunt.code_livre == "L002"
        assert emprunt.matricule == "E2026-001"
        assert emprunt.date_retour_prevue == "2026-10-15"

        # 3. Deuxième tentative : L002 par E2026-002 -> doit lever LivreDejaEmprunteError
        try:
            service.emprunter_livre(
                code_livre="L002",
                matricule="E2026-002",
                date_emprunt="2026-10-02"
            )
            assert False, "Aurait dû lever LivreDejaEmprunteError"
        except LivreDejaEmprunteError as e:
            assert "Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté" in str(e)

        # 4. Rendre le livre L002
        rendu = service.rendre_livre("L002", date_retour_effective="2026-10-10")
        assert rendu is True

        # 5. Maintenant que le livre est rendu, E2026-002 peut enfin l'emprunter !
        emprunt_2 = service.emprunter_livre(
            code_livre="L002",
            matricule="E2026-002",
            date_emprunt="2026-10-11"
        )
        assert emprunt_2.code_livre == "L002"
        assert emprunt_2.matricule == "E2026-002"

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_service_gestion_retards():
    """Vérifie la détection des emprunts en retard par le service."""
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = str(Path(temp_dir) / "test_retards.db")
        depot = DepotSqlite(db_path=db_path)
        service = BibliothequeService(depot=depot)

        # Emprunt le 01/10/2026 (retour prévu le 15/10/2026)
        service.emprunter_livre("L001", "E2026-099", date_emprunt="2026-10-01")

        # Au 15/10/2026 : aucun retard
        retards_j0 = service.lister_retards(date_reference="2026-10-15")
        assert len(retards_j0) == 0

        # Au 20/10/2026 : 1 retard détecté de 5 jours
        retards_j5 = service.lister_retards(date_reference="2026-10-20")
        assert len(retards_j5) == 1
        assert retards_j5[0]["emprunt"].code_livre == "L001"
        assert retards_j5[0]["jours_retard"] == 5

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_erreurs_livre_et_emprunt_inconnus():
    """Vérifie le déclenchement des erreurs pour les codes inconnus."""
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = str(Path(temp_dir) / "test_err.db")
        depot = DepotSqlite(db_path=db_path)
        service = BibliothequeService(depot=depot)

        # Livre inexistant
        try:
            service.emprunter_livre("L999", "E2026-001")
            assert False
        except LivreIntrouvableError:
            pass

        # Rendre un livre qui n'est pas emprunté
        try:
            service.rendre_livre("L001")
            assert False
        except EmpruntIntrouvableError:
            pass

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_scenario_diaporama_complet()
    test_service_gestion_retards()
    test_erreurs_livre_et_emprunt_inconnus()
    print("OK - test_service.py réussi !")

"""
Tests unitaires pour depot_sqlite.py.
Vérifie la persistance SQLite : recherche, enregistrement d'emprunt et de retour.
"""

import sys
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from depot_sqlite import DepotSqlite
from modeles import Emprunt


def test_recherche_mot_cle():
    """Vérifie la recherche 'Kourouma' identique à l'exemple de la console du prof."""
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = str(Path(temp_dir) / "test.db")
        depot = DepotSqlite(db_path=db_path)

        resultats = depot.rechercher_livres("Kourouma")
        codes = [livre.code for livre in resultats]
        assert "L002" in codes
        assert "L004" in codes
        assert len(resultats) == 2
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_emprunt_et_retour_sqlite():
    """Vérifie qu'un emprunt rend le livre indisponible puis disponible après retour."""
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = str(Path(temp_dir) / "test.db")
        depot = DepotSqlite(db_path=db_path)

        # Avant emprunt : disponible
        livre_initial = depot.obtenir_livre("L002")
        assert livre_initial is not None
        assert livre_initial.disponible is True

        # Enregistrement de l'emprunt
        emprunt = Emprunt("L002", "E2026-001", "2026-10-01", "2026-10-15")
        emprunt_sauve = depot.enregistrer_emprunt(emprunt)
        assert emprunt_sauve.id is not None

        # Après emprunt : indisponible
        livre_emprunte = depot.obtenir_livre("L002")
        assert livre_emprunte.disponible is False

        # Vérification dans les emprunts actifs
        actifs = depot.lister_emprunts_en_cours()
        assert any(e.code_livre == "L002" for e in actifs)

        # Enregistrement du retour
        ok = depot.enregistrer_retour("L002", "2026-10-14")
        assert ok is True

        # Après retour : à nouveau disponible
        livre_rendu = depot.obtenir_livre("L002")
        assert livre_rendu.disponible is True

        # Plus aucun emprunt actif pour L002
        actifs_apres = depot.lister_emprunts_en_cours()
        assert not any(e.code_livre == "L002" for e in actifs_apres)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_recherche_mot_cle()
    test_emprunt_et_retour_sqlite()
    print("OK - test_depot.py réussi !")

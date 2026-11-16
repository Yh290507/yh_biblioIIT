"""
Tests unitaires pour depot_sqlite.py.
Vérifie la persistance SQLite : recherche, enregistrement d'emprunt et de retour.
"""

import sys
import tempfile
import shutil
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from depot_sqlite import DepotSqlite
from modeles import Emprunt


class TestDepotSqlite(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test.db")
        self.depot = DepotSqlite(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_recherche_mot_cle(self):
        """Vérifie la recherche 'Kourouma' identique à l'exemple de la console du prof."""
        resultats = self.depot.rechercher_livres("Kourouma")
        codes = [livre.code for livre in resultats]
        self.assertIn("L002", codes)
        self.assertIn("L004", codes)
        self.assertEqual(len(resultats), 2)

    def test_emprunt_et_retour_sqlite(self):
        """Vérifie qu'un emprunt rend le livre indisponible puis disponible après retour."""
        # Avant emprunt : disponible
        livre_initial = self.depot.obtenir_livre("L002")
        self.assertIsNotNone(livre_initial)
        self.assertTrue(livre_initial.disponible)

        # Enregistrement de l'emprunt
        emprunt = Emprunt("L002", "E2026-001", "2026-10-01", "2026-10-15")
        emprunt_sauve = self.depot.enregistrer_emprunt(emprunt)
        self.assertIsNotNone(emprunt_sauve.id)

        # Après emprunt : indisponible
        livre_emprunte = self.depot.obtenir_livre("L002")
        self.assertFalse(livre_emprunte.disponible)

        # Vérification dans les emprunts actifs
        actifs = self.depot.lister_emprunts_en_cours()
        self.assertTrue(any(e.code_livre == "L002" for e in actifs))

        # Enregistrement du retour
        ok = self.depot.enregistrer_retour("L002", "2026-10-14")
        self.assertTrue(ok)

        # Après retour : à nouveau disponible
        livre_rendu = self.depot.obtenir_livre("L002")
        self.assertTrue(livre_rendu.disponible)

        # Plus aucun emprunt actif pour L002
        actifs_apres = self.depot.lister_emprunts_en_cours()
        self.assertFalse(any(e.code_livre == "L002" for e in actifs_apres))


if __name__ == "__main__":
    unittest.main()

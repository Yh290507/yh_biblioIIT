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
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from depot_sqlite import DepotSqlite
from service import BibliothequeService
from regles import LivreDejaEmprunteError, LivreIntrouvableError, EmpruntIntrouvableError


class TestService(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_service.db")
        self.depot = DepotSqlite(db_path=self.db_path)
        self.service = BibliothequeService(depot=self.depot)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scenario_diaporama_complet(self):
        """Reproduit fidèlement la session console réelle du professeur."""
        # 1. Recherche : Kourouma -> doit retourner L004 et L002
        resultats = self.service.rechercher_livres("Kourouma")
        self.assertEqual(len(resultats), 2)
        self.assertTrue(any(l.code == "L004" for l in resultats))
        self.assertTrue(any(l.code == "L002" for l in resultats))

        # 2. Emprunt : L002 par E2026-001 à la date 01/10/2026 -> retour prévu 15/10/2026
        emprunt = self.service.emprunter_livre(
            code_livre="L002",
            matricule="E2026-001",
            date_emprunt="2026-10-01"
        )
        self.assertEqual(emprunt.code_livre, "L002")
        self.assertEqual(emprunt.matricule, "E2026-001")
        self.assertEqual(emprunt.date_retour_prevue, "2026-10-15")

        # 3. Deuxième tentative : L002 par E2026-002 -> doit lever LivreDejaEmprunteError
        with self.assertRaises(LivreDejaEmprunteError) as ctx:
            self.service.emprunter_livre(
                code_livre="L002",
                matricule="E2026-002",
                date_emprunt="2026-10-02"
            )
        self.assertIn(
            "Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté",
            str(ctx.exception)
        )

        # 4. Rendre le livre L002
        rendu = self.service.rendre_livre("L002", date_retour_effective="2026-10-10")
        self.assertTrue(rendu)

        # 5. Maintenant que le livre est rendu, E2026-002 peut enfin l'emprunter !
        emprunt_2 = self.service.emprunter_livre(
            code_livre="L002",
            matricule="E2026-002",
            date_emprunt="2026-10-11"
        )
        self.assertEqual(emprunt_2.code_livre, "L002")
        self.assertEqual(emprunt_2.matricule, "E2026-002")

    def test_service_gestion_retards(self):
        """Vérifie la détection des emprunts en retard par le service."""
        # Emprunt le 01/10/2026 (retour prévu le 15/10/2026)
        self.service.emprunter_livre("L001", "E2026-099", date_emprunt="2026-10-01")

        # Au 15/10/2026 : aucun retard
        retards_j0 = self.service.lister_retards(date_reference="2026-10-15")
        self.assertEqual(len(retards_j0), 0)

        # Au 20/10/2026 : 1 retard détecté de 5 jours
        retards_j5 = self.service.lister_retards(date_reference="2026-10-20")
        self.assertEqual(len(retards_j5), 1)
        self.assertEqual(retards_j5[0]["emprunt"].code_livre, "L001")
        self.assertEqual(retards_j5[0]["jours_retard"], 5)

    def test_erreurs_livre_et_emprunt_inconnus(self):
        """Vérifie le déclenchement des erreurs pour les codes inconnus."""
        # Livre inexistant
        with self.assertRaises(LivreIntrouvableError):
            self.service.emprunter_livre("L999", "E2026-001")

        # Rendre un livre qui n'est pas emprunté
        with self.assertRaises(EmpruntIntrouvableError):
            self.service.rendre_livre("L001")


if __name__ == "__main__":
    unittest.main()

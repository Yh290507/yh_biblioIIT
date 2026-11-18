"""
Tests unitaires et d'intégration pour service.py.
Valide le scénario complet présenté sur la diapositive du professeur :
1. Recherche par mot-clé (Kourouma)
2. Emprunt avec succès (L002 par E2026-001)
3. Blocage si réemprunt (L002 par E2026-002) avec le message exact
4. Retour du livre et restitution de sa disponibilité
5. Détection des retards
Ainsi que les fonctionnalités professionnelles de SIGB (lecteurs, quotas, stats, suppression sécurisée).
"""

import sys
import tempfile
import shutil
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from depot_sqlite import DepotSqlite
from service import BibliothequeService
from regles import (
    LivreDejaEmprunteError,
    LivreIntrouvableError,
    EmpruntIntrouvableError,
    QuotaEmpruntsDepasseError,
    SuppressionImpossibleError,
)


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

        # 3. Deuxième tentative : L002 par E2026-002 -> doit lever LivreDejaEmprunteError (1 seul exemplaire)
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

    def test_quota_emprunts_service(self):
        """Vérifie que le service applique le quota de 3 livres maximum par étudiant."""
        # Emprunter 3 livres distincts
        self.service.emprunter_livre("L001", "E2026-050", date_emprunt="2026-10-01")
        self.service.emprunter_livre("L003", "E2026-050", date_emprunt="2026-10-01")
        self.service.emprunter_livre("L004", "E2026-050", date_emprunt="2026-10-01")

        # Tentative du 4ème emprunt -> QuotaEmpruntsDepasseError
        with self.assertRaises(QuotaEmpruntsDepasseError):
            self.service.emprunter_livre("L005", "E2026-050", date_emprunt="2026-10-01")

    def test_gestion_lecteurs_service(self):
        """Vérifie l'inscription, la recherche et l'obtention d'un lecteur."""
        lecteur = self.service.inscrire_lecteur("E2026-999", "KONE", "Bakary", "0700000000", "Data Science")
        self.assertEqual(lecteur.matricule, "E2026-999")

        trouve = self.service.obtenir_lecteur("E2026-999")
        self.assertEqual(trouve.nom, "KONE")

        resultats = self.service.rechercher_lecteurs("Bakary")
        self.assertEqual(len(resultats), 1)

    def test_protection_suppression_si_historique(self):
        """Vérifie qu'un livre ou lecteur avec historique ne peut pas être supprimé."""
        self.service.emprunter_livre("L001", "E2026-001")

        # Tentative de suppression du livre L001
        with self.assertRaises(SuppressionImpossibleError):
            self.service.supprimer_livre("L001")

        # Tentative de suppression du lecteur E2026-001
        with self.assertRaises(SuppressionImpossibleError):
            self.service.supprimer_lecteur("E2026-001")

    def test_statistiques_et_export_csv(self):
        """Vérifie le calcul des statistiques et l'export CSV."""
        stats = self.service.obtenir_statistiques()
        self.assertGreaterEqual(stats["nb_titres"], 25)
        self.assertGreaterEqual(stats["nb_exemplaires_total"], 25)

        # Emprunter un livre avec retard pour tester l'export CSV
        self.service.emprunter_livre("L001", "E2026-001", date_emprunt="2026-01-01")
        csv_file = str(Path(self.temp_dir) / "test_retards.csv")
        chemin = self.service.exporter_retards_csv(csv_file)
        self.assertTrue(Path(chemin).is_file())


if __name__ == "__main__":
    unittest.main()

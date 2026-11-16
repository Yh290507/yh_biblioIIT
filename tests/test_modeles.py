"""
Tests unitaires pour modeles.py.
Vérifie la création des objets Livre et Emprunt ainsi que leurs méthodes.
"""

import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modeles import Livre, Emprunt


class TestModeles(unittest.TestCase):

    def test_creation_livre(self):
        """Vérifie la création et l'affichage d'un livre conforme au slide."""
        livre = Livre("L004", "Allah n'est pas obligé", "Ahmadou Kourouma", 2000)
        self.assertEqual(livre.code, "L004")
        self.assertEqual(livre.titre, "Allah n'est pas obligé")
        self.assertEqual(livre.auteur, "Ahmadou Kourouma")
        self.assertEqual(livre.annee, 2000)
        self.assertTrue(livre.disponible)
        self.assertEqual(str(livre), "L004  Allah n'est pas obligé - Ahmadou Kourouma (2000)")

    def test_creation_emprunt(self):
        """Vérifie la création d'un emprunt en cours."""
        emprunt = Emprunt(
            code_livre="L002",
            matricule="E2026-001",
            date_emprunt=date(2026, 10, 1),
            date_retour_prevue=date(2026, 10, 15)
        )
        self.assertEqual(emprunt.code_livre, "L002")
        self.assertEqual(emprunt.matricule, "E2026-001")
        self.assertTrue(emprunt.est_en_cours())
        self.assertIsNone(emprunt.date_retour_effective)

    def test_retour_emprunt(self):
        """Vérifie la clôture d'un emprunt lors du retour effectif."""
        emprunt = Emprunt(
            code_livre="L002",
            matricule="E2026-001",
            date_emprunt="2026-10-01",
            date_retour_prevue="2026-10-15",
            date_retour_effective="2026-10-14"
        )
        self.assertFalse(emprunt.est_en_cours())


if __name__ == "__main__":
    unittest.main()

"""
Tests unitaires pour regles.py.
Vérifie le calcul des dates de retour, la détection des retards et le blocage si déjà emprunté.
"""

import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modeles import Livre, Emprunt
from regles import (
    calculer_date_retour,
    est_en_retard,
    calculer_jours_retard,
    verifier_livre_disponible,
    LivreDejaEmprunteError,
)


class TestRegles(unittest.TestCase):

    def test_calcul_date_retour(self):
        """Vérifie que la date de retour est bien à J + 14 par défaut."""
        d_emprunt = date(2026, 10, 1)
        d_retour = calculer_date_retour(d_emprunt, duree_jours=14)
        self.assertEqual(d_retour, date(2026, 10, 15))

    def test_detection_retard(self):
        """Vérifie qu'un retard est correctement détecté après la date limite."""
        emprunt = Emprunt(
            code_livre="L002",
            matricule="E2026-001",
            date_emprunt="2026-10-01",
            date_retour_prevue="2026-10-15"
        )
        # À la date limite : aucun retard
        self.assertFalse(est_en_retard(emprunt, date_reference="2026-10-15"))
        self.assertEqual(calculer_jours_retard(emprunt, date_reference="2026-10-15"), 0)

        # Lendemain : 1 jour de retard
        self.assertTrue(est_en_retard(emprunt, date_reference="2026-10-16"))
        self.assertEqual(calculer_jours_retard(emprunt, date_reference="2026-10-16"), 1)

        # 5 jours après : 5 jours de retard
        self.assertEqual(calculer_jours_retard(emprunt, date_reference="2026-10-20"), 5)

    def test_livre_deja_emprunte_leve_exception(self):
        """Vérifie qu'emprunter un livre déjà emprunté lève le message exact de la console."""
        livre = Livre("L002", "Les Soleils des indépendances", "Ahmadou Kourouma", 1968)
        emprunt_actif = Emprunt("L002", "E2026-001", "2026-10-01", "2026-10-15")

        with self.assertRaises(LivreDejaEmprunteError) as ctx:
            verifier_livre_disponible(livre, [emprunt_actif])

        self.assertIn(
            "Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté",
            str(ctx.exception)
        )


if __name__ == "__main__":
    unittest.main()

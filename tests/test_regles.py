"""
Tests unitaires pour regles.py.
Vérifie le calcul des dates de retour, la détection des retards, le blocage si déjà emprunté,
ainsi que les règles de gestion professionnelles (quotas, non-doublon, blocage retardataire).
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
    verifier_quota_lecteur,
    verifier_lecteur_sans_retard,
    verifier_non_doublon_emprunt,
    LivreDejaEmprunteError,
    QuotaEmpruntsDepasseError,
    LecteurAvecRetardBloqueError,
    LivreDejaEnCoursParLecteurError,
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
        livre = Livre("L002", "Les Soleils des indépendances", "Ahmadou Kourouma", 1968, nb_exemplaires=1)
        emprunt_actif = Emprunt("L002", "E2026-001", "2026-10-01", "2026-10-15")

        with self.assertRaises(LivreDejaEmprunteError) as ctx:
            verifier_livre_disponible(livre, [emprunt_actif])

        self.assertIn(
            "Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté",
            str(ctx.exception)
        )

    def test_quota_emprunts_depasse(self):
        """Vérifie que la règle du quota maximal (ex: 3 livres) bloque le 4ème emprunt."""
        emprunts_actifs = [
            Emprunt("L001", "E2026-001", "2026-10-01", "2026-10-15"),
            Emprunt("L003", "E2026-001", "2026-10-01", "2026-10-15"),
            Emprunt("L004", "E2026-001", "2026-10-01", "2026-10-15"),
        ]
        with self.assertRaises(QuotaEmpruntsDepasseError):
            verifier_quota_lecteur("E2026-001", emprunts_actifs, max_autorise=3)

    def test_lecteur_avec_retard_bloque(self):
        """Vérifie qu'un étudiant ayant un prêt en retard ne peut pas emprunter."""
        emprunt_en_retard = Emprunt("L001", "E2026-001", "2026-10-01", "2026-10-15")
        with self.assertRaises(LecteurAvecRetardBloqueError):
            verifier_lecteur_sans_retard("E2026-001", [emprunt_en_retard], date_ref="2026-10-20")

    def test_doublon_emprunt_meme_livre(self):
        """Vérifie qu'un étudiant ne peut pas emprunter 2 fois le même livre en même temps."""
        livre = Livre("L001", "Climbié", "Bernard Dadié", 1956, nb_exemplaires=3)
        emprunts_actifs = [Emprunt("L001", "E2026-001", "2026-10-01", "2026-10-15")]
        with self.assertRaises(LivreDejaEnCoursParLecteurError):
            verifier_non_doublon_emprunt(livre, emprunts_actifs)


if __name__ == "__main__":
    unittest.main()

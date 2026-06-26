# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from database import get_connection
from datetime import datetime

def fermer_seances_expirees():
    """
    Vérifie toutes les séances ouvertes.
    Si heure_fin_prevue est dépassée → ferme la séance et marque
    absent tous les étudiants de la classe qui n'ont pas de présence.
    Cette fonction est appelée automatiquement toutes les 60 secondes.
    """
    maintenant = datetime.now()
    maintenant_str = maintenant.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    # ── 1. Trouver toutes les séances ouvertes dont l'heure est dépassée ──────
    seances_expirees = cursor.execute("""
        SELECT s.*, e.classe_id
        FROM seances s
        JOIN emploi_du_temps e ON s.edt_id = e.id
        WHERE s.statut = 'ouverte'
          AND s.heure_fin_prevue <= ?
    """, (maintenant_str,)).fetchall()

    if not seances_expirees:
        conn.close()
        return  # Rien à faire

    for seance in seances_expirees:
        seance_id  = seance["id"]
        classe_id  = seance["classe_id"]

        print(f"[SCHEDULER] Fermeture automatique — séance ID {seance_id}")

        # ── 2. Récupérer tous les étudiants de cette classe ───────────────────
        etudiants = cursor.execute("""
            SELECT id FROM etudiants
            WHERE classe_id = ? AND actif = 1
        """, (classe_id,)).fetchall()

        # ── 3. Pour chaque étudiant, vérifier s'il a une présence ─────────────
        for etudiant in etudiants:
            etudiant_id = etudiant["id"]

            presence_existante = cursor.execute("""
                SELECT id FROM presences
                WHERE seance_id = ? AND etudiant_id = ?
            """, (seance_id, etudiant_id)).fetchone()

            # S'il n'a pas de présence → insérer "absent"
            if not presence_existante:
                cursor.execute("""
                    INSERT INTO presences
                        (seance_id, etudiant_id, timestamp_scan, methode, statut, valide_par_prof)
                    VALUES (?, ?, ?, 'auto', 'absent', 0)
                """, (seance_id, etudiant_id, maintenant_str))

                print(f"[SCHEDULER] Étudiant ID {etudiant_id} → absent")

        # ── 4. Fermer la séance ────────────────────────────────────────────────
        cursor.execute("""
            UPDATE seances
            SET statut = 'fermee',
                heure_fin_reelle = ?
            WHERE id = ?
        """, (maintenant_str, seance_id))

        print(f"[SCHEDULER] Séance ID {seance_id} fermée à {maintenant_str}")

    conn.commit()
    conn.close()


def demarrer_scheduler():
    """
    Crée et démarre le scheduler en arrière-plan.
    Appelée une seule fois au démarrage du serveur dans app.py.
    """
    scheduler = BackgroundScheduler()

    # Exécuter fermer_seances_expirees() toutes les 60 secondes
    scheduler.add_job(
        func=fermer_seances_expirees,
        trigger="interval",
        seconds=60,
        id="fermeture_auto",
        name="Fermeture automatique des séances expirées"
    )

    scheduler.start()
    print("[SCHEDULER] Démarré — vérification toutes les 60 secondes")

    return scheduler
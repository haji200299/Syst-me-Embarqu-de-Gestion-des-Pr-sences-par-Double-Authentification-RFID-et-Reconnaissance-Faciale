# simuler_historique.py — version avec dashboard garanti
from database import get_connection
from datetime import datetime, timedelta
import hashlib
import random

conn = get_connection()

# Desactiver temporairement les clés etrangeres pour le nettoyage
conn.execute("PRAGMA foreign_keys = OFF")

conn.execute("DELETE FROM alertes")
conn.execute("DELETE FROM presences")
conn.execute("DELETE FROM seances")
conn.execute("DELETE FROM emploi_du_temps")
conn.execute("DELETE FROM etudiants")
conn.execute("DELETE FROM profs")
conn.execute("DELETE FROM classes")
conn.execute("DELETE FROM salles")
conn.execute("DELETE FROM gestionnaire")

# Reactiver les clés etrangeres
conn.execute("PRAGMA foreign_keys = ON")

conn.commit()
print("Anciennes donnees supprimees")

# ── Classes ────────────────────────────────────────────────────────────────
conn.execute("INSERT INTO classes (id, nom, niveau, filiere) VALUES (1, 'INFO-2A', 'Bac+2', 'Informatique')")
conn.execute("INSERT INTO classes (id, nom, niveau, filiere) VALUES (2, 'INFO-2B', 'Bac+2', 'Informatique')")

# ── Salles ─────────────────────────────────────────────────────────────────
conn.execute("""
    INSERT INTO salles (id, nom, batiment, raspberry_ip, esp32_ip)
    VALUES (1, 'Salle 101', 'Batiment A', '192.168.137.198', '192.168.137.64')
""")

# ── Profs ──────────────────────────────────────────────────────────────────
conn.execute("""
    INSERT INTO profs (id, nom, prenom, rfid_uid, matiere)
    VALUES (1, 'Benali', 'Hassan', '93E8F32F', 'Reseaux / Securite')
""")
conn.execute("""
    INSERT INTO profs (id, nom, prenom, rfid_uid, matiere)
    VALUES (2, 'Meziani', 'Sara', 'D95AB8B8', 'Systemes / Base de donnees')
""")

# ── Etudiants ──────────────────────────────────────────────────────────────
etudiants_2a = [
    (1, 'Haji',    'Mohammed', '45DA8E2A'),
    (2, 'Alaoui',  'Youssef',  'D32FF814'),
    (3, 'Bennani', 'Fatima',   'D07FF51B'),
]
etudiants_2b = [
    (4, 'Idrissi', 'Karim',  'F3E79211'),
    (5, 'Tazi',    'Nadia',  '3AA15124'),
]

for eid, nom, prenom, rfid in etudiants_2a:
    conn.execute(
        "INSERT INTO etudiants (id, nom, prenom, rfid_uid, classe_id) VALUES (?, ?, ?, ?, 1)",
        (eid, nom, prenom, rfid)
    )
for eid, nom, prenom, rfid in etudiants_2b:
    conn.execute(
        "INSERT INTO etudiants (id, nom, prenom, rfid_uid, classe_id) VALUES (?, ?, ?, ?, 2)",
        (eid, nom, prenom, rfid)
    )

conn.commit()

# ── EDT — IMPORTANT : le jour_semaine est calcule sur AUJOURD'HUI ─────────
# Pour garantir que le dashboard affiche des seances aujourd'hui,
# on cree les creneaux recurrents sur le jour actuel et un autre jour
aujourd_hui   = datetime.now()
jour_actuel   = aujourd_hui.weekday()       # 0=lundi ... 6=dimanche
jour_secondaire = (jour_actuel + 2) % 7     # un autre jour de la semaine

# EDT 1 : INFO-2A - Reseaux - AUJOURD'HUI a 08:00 - Salle 101 - Benali
conn.execute("""
    INSERT INTO emploi_du_temps (id, salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (1, 1, 1, 1, ?, '08:00', '09:30', 'Reseaux')
""", (jour_actuel,))

# EDT 2 : INFO-2B - Systemes - AUJOURD'HUI a 10:00 - Salle 101 - Meziani
conn.execute("""
    INSERT INTO emploi_du_temps (id, salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (2, 1, 2, 2, ?, '10:00', '11:30', 'Systemes')
""", (jour_actuel,))

# EDT 3 : INFO-2A - Securite - jour secondaire a 08:00 - Salle 101 - Benali
conn.execute("""
    INSERT INTO emploi_du_temps (id, salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (3, 1, 1, 1, ?, '08:00', '09:30', 'Securite')
""", (jour_secondaire,))

# EDT 4 : INFO-2B - Base de donnees - jour secondaire a 10:00 - Salle 101 - Meziani
conn.execute("""
    INSERT INTO emploi_du_temps (id, salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (4, 1, 2, 2, ?, '10:00', '11:30', 'Base de donnees')
""", (jour_secondaire,))

conn.commit()
print(f"EDT cree pour jour_actuel={jour_actuel} et jour_secondaire={jour_secondaire}")

edts = [
    {"id": 1, "jour": jour_actuel,     "heure": "08:00", "classe_id": 1, "etudiants": etudiants_2a},
    {"id": 2, "jour": jour_actuel,     "heure": "10:00", "classe_id": 2, "etudiants": etudiants_2b},
    {"id": 3, "jour": jour_secondaire, "heure": "08:00", "classe_id": 1, "etudiants": etudiants_2a},
    {"id": 4, "jour": jour_secondaire, "heure": "10:00", "classe_id": 2, "etudiants": etudiants_2b},
]

seance_id_counter   = 1
presence_id_counter = 1

# ── Historique des 21 derniers jours (hors aujourd'hui) ────────────────────
for jour_offset in range(21, 0, -1):
    date_jour    = aujourd_hui - timedelta(days=jour_offset)
    jour_semaine = date_jour.weekday()

    for edt in edts:
        if edt["jour"] != jour_semaine:
            continue

        heure_h, heure_m = map(int, edt["heure"].split(":"))
        decalage_prof = random.randint(-1, 3)
        debut_reel = date_jour.replace(hour=heure_h, minute=heure_m, second=0, microsecond=0)
        debut_reel += timedelta(minutes=decalage_prof)
        fin_prevue  = debut_reel + timedelta(minutes=90)

        conn.execute("""
            INSERT INTO seances
                (id, edt_id, date, heure_debut_reelle, heure_fin_prevue, heure_fin_reelle, statut, ouverte_par_rfid)
            VALUES (?, ?, ?, ?, ?, ?, 'fermee', ?)
        """, (
            seance_id_counter, edt["id"], date_jour.strftime("%Y-%m-%d"),
            debut_reel.strftime("%Y-%m-%d %H:%M:%S"),
            fin_prevue.strftime("%Y-%m-%d %H:%M:%S"),
            fin_prevue.strftime("%Y-%m-%d %H:%M:%S"),
            "93E8F32F" if edt["classe_id"] == 1 else "D95AB8B8"
        ))

        for eid, nom, prenom, rfid in edt["etudiants"]:
            rand = random.random()
            if rand < 0.80:
                statut_p, minutes_retard = "present", random.randint(0, 3)
            elif rand < 0.95:
                statut_p, minutes_retard = "retard", random.randint(4, 8)
            else:
                statut_p, minutes_retard = "absent", None

            if statut_p != "absent":
                ts = (debut_reel + timedelta(minutes=minutes_retard)).strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("""
                    INSERT INTO presences (id, seance_id, etudiant_id, timestamp_scan, methode, statut, valide_par_prof)
                    VALUES (?, ?, ?, ?, 'rfid+visage', ?, 0)
                """, (presence_id_counter, seance_id_counter, eid, ts, statut_p))
            else:
                ts = fin_prevue.strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("""
                    INSERT INTO presences (id, seance_id, etudiant_id, timestamp_scan, methode, statut, valide_par_prof)
                    VALUES (?, ?, ?, ?, 'auto', 'absent', 0)
                """, (presence_id_counter, seance_id_counter, eid, ts))
            presence_id_counter += 1

        seance_id_counter += 1

conn.commit()
print(f"{seance_id_counter - 1} seances d'historique generees")

# ── SEANCES D'AUJOURD'HUI — pour remplir le dashboard ──────────────────────
# Seance 1 : INFO-2A - deja terminee ce matin (fermee, avec presences completes)
debut_1 = aujourd_hui.replace(hour=8, minute=0, second=0, microsecond=0)
fin_1   = debut_1 + timedelta(minutes=90)
statut_1 = "fermee" if aujourd_hui > fin_1 else "ouverte"

conn.execute("""
    INSERT INTO seances (id, edt_id, date, heure_debut_reelle, heure_fin_prevue, heure_fin_reelle, statut, ouverte_par_rfid)
    VALUES (?, 1, ?, ?, ?, ?, ?, '93E8F32F')
""", (
    seance_id_counter, aujourd_hui.strftime("%Y-%m-%d"),
    debut_1.strftime("%Y-%m-%d %H:%M:%S"), fin_1.strftime("%Y-%m-%d %H:%M:%S"),
    fin_1.strftime("%Y-%m-%d %H:%M:%S") if statut_1 == "fermee" else None,
    statut_1
))
seance_aujourdhui_1 = seance_id_counter
seance_id_counter += 1

for eid, nom, prenom, rfid in etudiants_2a:
    rand = random.random()
    if rand < 0.80:
        statut_p, mins = "present", random.randint(0, 3)
    elif rand < 0.95:
        statut_p, mins = "retard", random.randint(4, 8)
    else:
        statut_p, mins = "absent", None

    if statut_p != "absent":
        ts = (debut_1 + timedelta(minutes=mins)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO presences (id, seance_id, etudiant_id, timestamp_scan, methode, statut, valide_par_prof)
            VALUES (?, ?, ?, ?, 'rfid+visage', ?, 0)
        """, (presence_id_counter, seance_aujourdhui_1, eid, ts, statut_p))
    else:
        ts = fin_1.strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO presences (id, seance_id, etudiant_id, timestamp_scan, methode, statut, valide_par_prof)
            VALUES (?, ?, ?, ?, 'auto', 'absent', 0)
        """, (presence_id_counter, seance_aujourdhui_1, eid, ts))
    presence_id_counter += 1

# Seance 2 : INFO-2B - EN COURS maintenant (ouverte) pour montrer le statut actif
debut_2 = aujourd_hui - timedelta(minutes=5)  # ouverte il y a 5 min
fin_2   = debut_2 + timedelta(minutes=90)

conn.execute("""
    INSERT INTO seances (id, edt_id, date, heure_debut_reelle, heure_fin_prevue, heure_fin_reelle, statut, ouverte_par_rfid)
    VALUES (?, 2, ?, ?, ?, NULL, 'ouverte', 'D95AB8B8')
""", (
    seance_id_counter, aujourd_hui.strftime("%Y-%m-%d"),
    debut_2.strftime("%Y-%m-%d %H:%M:%S"), fin_2.strftime("%Y-%m-%d %H:%M:%S")
))
seance_aujourdhui_2 = seance_id_counter
seance_id_counter += 1

# Quelques etudiants 2B deja presents dans cette seance en cours
for eid, nom, prenom, rfid in etudiants_2b:
    if random.random() < 0.7:  # 70% deja scannes
        statut_p = "present" if random.random() < 0.8 else "retard"
        mins = random.randint(0, 3) if statut_p == "present" else random.randint(4, 8)
        ts = (debut_2 + timedelta(minutes=mins)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO presences (id, seance_id, etudiant_id, timestamp_scan, methode, statut, valide_par_prof)
            VALUES (?, ?, ?, ?, 'rfid+visage', ?, 0)
        """, (presence_id_counter, seance_aujourdhui_2, eid, ts, statut_p))
        presence_id_counter += 1

conn.commit()
print("Seances d'aujourd'hui creees (1 fermee + 1 en cours) -> dashboard rempli")

# ── Alertes ──────────────────────────────────────────────────────────────
dates_alertes = [aujourd_hui - timedelta(days=5), aujourd_hui - timedelta(hours=2)]
for i, date_a in enumerate(dates_alertes):
    conn.execute("""
        INSERT INTO alertes (seance_id, type_alerte, rfid_scanne, visage_detecte, description, timestamp, traitee)
        VALUES (?, 'fraude', ?, ?, ?, ?, ?)
    """, (
        seance_aujourdhui_1,
        "D32FF814" if i == 0 else "F3E79211",
        "3" if i == 0 else "5",
        "Badge etudiant utilise par un autre etudiant",
        date_a.strftime("%Y-%m-%d %H:%M:%S"),
        1 if i == 0 else 0
    ))
conn.commit()
print("Alertes ajoutees (1 traitee + 1 non traitee aujourd'hui)")

# ── Gestionnaire ────────────────────────────────────────────────────────────
mdp_hash = hashlib.sha256("admin123".encode()).hexdigest()
conn.execute("INSERT INTO gestionnaire (login, password_hash, nom) VALUES ('gestionnaire', ?, 'Mme Administratrice')", (mdp_hash,))
conn.commit()
conn.close()

print()
print("="*50)
print("SIMULATION TERMINEE - DASHBOARD REMPLI")
print("="*50)
print("URL   : http://localhost:5000")
print("Login : gestionnaire")
print("Mdp   : admin123")
print()
print("Le dashboard affichera 2 seances aujourd'hui :")
print("  1. INFO-2A Reseaux  -> FERMEE  (avec stats completes)")
print("  2. INFO-2B Systemes -> OUVERTE (en cours, quelques presences)")
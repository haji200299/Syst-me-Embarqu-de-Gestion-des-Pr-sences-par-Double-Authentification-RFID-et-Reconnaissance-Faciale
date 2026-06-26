# setup_final.py
from database import get_connection
from datetime import datetime, timedelta
import hashlib

conn = get_connection()

# Nettoyer
conn.execute("DELETE FROM presences")
conn.execute("DELETE FROM seances")
conn.execute("DELETE FROM emploi_du_temps")
conn.execute("DELETE FROM etudiants")
conn.execute("DELETE FROM profs")
conn.execute("DELETE FROM classes")
conn.execute("DELETE FROM salles")
conn.execute("DELETE FROM alertes")
conn.execute("DELETE FROM gestionnaire")

print("Anciennes donnees supprimees")

# ── Classes ────────────────────────────────────────────────────────────
conn.execute("INSERT INTO classes (id, nom, niveau, filiere) VALUES (1, 'INFO-2A', 'Bac+2', 'Informatique')")
conn.execute("INSERT INTO classes (id, nom, niveau, filiere) VALUES (2, 'INFO-2B', 'Bac+2', 'Informatique')")

# ── Salles ─────────────────────────────────────────────────────────────
conn.execute("""
    INSERT INTO salles (id, nom, batiment, raspberry_ip, esp32_ip)
    VALUES (1, 'Salle 101', 'Batiment A', '192.168.137.198', '192.168.137.1')
""")

# ── Profs ──────────────────────────────────────────────────────────────
# Un prof peut enseigner plusieurs matieres
conn.execute("""
    INSERT INTO profs (id, nom, prenom, rfid_uid, matiere)
    VALUES (1, 'Benali', 'Hassan', '93E8F32F', 'Reseaux / Securite')
""")
conn.execute("""
    INSERT INTO profs (id, nom, prenom, rfid_uid, matiere)
    VALUES (2, 'Meziani', 'Sara', 'D95AB8B8', 'Systemes / Base de donnees')
""")

# ── Etudiants ──────────────────────────────────────────────────────────
# Classe INFO-2A — 3 etudiants
conn.execute("""
    INSERT INTO etudiants (id, nom, prenom, rfid_uid, classe_id)
    VALUES (1, 'Haji', 'Mohammed', '3AA15124', 1)
""")
conn.execute("""
    INSERT INTO etudiants (id, nom, prenom, rfid_uid, classe_id)
    VALUES (2, 'Alaoui', 'Youssef', '45DA8E2A', 1)
""")
conn.execute("""
    INSERT INTO etudiants (id, nom, prenom, rfid_uid, classe_id)
    VALUES (3, 'Bennani', 'Rayan', 'D07FF51B', 1)
""")

# Classe INFO-2B — 2 etudiants
conn.execute("""
    INSERT INTO etudiants (id, nom, prenom, rfid_uid, classe_id)
    VALUES (4, 'Idrissi', 'Karim', 'D32FF814', 2)
""")
conn.execute("""
    INSERT INTO etudiants (id, nom, prenom, rfid_uid, classe_id)
    VALUES (5, 'Tazi', 'Otmane', 'F3E79211', 2)
""")

# ── EDT ────────────────────────────────────────────────────────────────
# Heure actuelle pour le test
maintenant  = datetime.now()
jour        = maintenant.weekday()

# Creneau 1 — INFO-2A maintenant (8 min)
h1_debut = maintenant.strftime("%H:%M")
h1_fin   = (maintenant + timedelta(minutes=8)).strftime("%H:%M")

# Creneau 2 — INFO-2B dans 10 min (8 min)
h2_debut = (maintenant + timedelta(minutes=10)).strftime("%H:%M")
h2_fin   = (maintenant + timedelta(minutes=18)).strftime("%H:%M")

# Creneau 3 — INFO-2A demain meme heure — autre matiere meme prof
h3_debut = maintenant.strftime("%H:%M")
h3_fin   = (maintenant + timedelta(minutes=8)).strftime("%H:%M")
jour_demain = (jour + 1) % 6  # jour suivant (max samedi)

# Salle 101 — INFO-2A — Reseaux — Prof Benali
conn.execute("""
    INSERT INTO emploi_du_temps
        (salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (1, 1, 1, ?, ?, ?, 'Reseaux')
""", (jour, h1_debut, h1_fin))

# Salle 101 — INFO-2B — Securite — Prof Benali (meme prof, autre matiere, autre heure)
conn.execute("""
    INSERT INTO emploi_du_temps
        (salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (1, 2, 2, ?, ?, ?, 'Systemes')
""", (jour, h2_debut, h2_fin))

# Salle 101 — INFO-2A — Securite — Prof Benali (meme prof, matiere differente, jour different)
conn.execute("""
    INSERT INTO emploi_du_temps
        (salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (1, 1, 1, ?, ?, ?, 'Securite')
""", (jour_demain, h3_debut, h3_fin))

# Salle 101 — INFO-2B — Base de donnees — Prof Meziani (jour different)
conn.execute("""
    INSERT INTO emploi_du_temps
        (salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (1, 2, 2, ?, ?, ?, 'Base de donnees')
""", (jour_demain, h3_debut, h3_fin))

# ── Gestionnaire ───────────────────────────────────────────────────────
mdp_hash = hashlib.sha256("admin123".encode()).hexdigest()
conn.execute("""
    INSERT INTO gestionnaire (login, password_hash, nom)
    VALUES ('gestionnaire', ?, 'Mme Administratrice')
""", (mdp_hash,))

conn.commit()
conn.close()

print("=" * 50)
print("Donnees inserees avec succes !")
print("=" * 50)
print()
print("PROFS :")
print("  Hassan Benali  (93E8F32F) -> Reseaux + Securite")
print("  Sara Meziani   (D95AB8B8) -> Systemes + Base de donnees")
print()
print("CLASSES :")
print("  INFO-2A (3 etudiants) :")
print("    Mohammed Haji    -> 45DA8E2A")
print("    Youssef Alaoui   -> D32FF814")
print("    Fatima Bennani   -> D07FF51B")
print()
print("  INFO-2B (2 etudiants) :")
print("    Karim Idrissi    -> F3E79211")
print("    Nadia Tazi       -> 3AA15124")
print()
print("EDT AUJOURD'HUI (Salle 101) :")
print(f"  {h1_debut} -> {h1_fin}  | INFO-2A | Reseaux   | Prof Benali")
print(f"  {h2_debut} -> {h2_fin}  | INFO-2B | Systemes  | Prof Meziani")
print()
print("EDT DEMAIN (Salle 101) :")
print(f"  {h3_debut} -> {h3_fin}  | INFO-2A | Securite       | Prof Benali")
print(f"  {h3_debut} -> {h3_fin}  | INFO-2B | Base donnees   | Prof Meziani")
print()
print("SEUILS :")
print("  0-3 min  -> Present")
print("  3-8 min  -> Retard")
print("  apres 8 min -> Absent (fermeture auto)")
print()
print("GESTIONNAIRE :")
print("  login : gestionnaire")
print("  mdp   : admin123")
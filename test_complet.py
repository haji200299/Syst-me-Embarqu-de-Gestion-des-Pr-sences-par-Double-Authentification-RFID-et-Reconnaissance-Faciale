# test_complet_insert.py
from database import get_connection
from datetime import datetime
import hashlib

conn = get_connection()
maintenant = datetime.now()

# Jour actuel et heure actuelle
jour = maintenant.weekday()  # 0=lundi
heure_debut = maintenant.strftime("%H:%M")

from datetime import timedelta
heure_fin = (maintenant + timedelta(minutes=90)).strftime("%H:%M")

print("Insertion des donnees de test...")
print(f"Jour={jour}, Heure={heure_debut} -> {heure_fin}")

# Classes
conn.execute("""
    INSERT OR IGNORE INTO classes (id, nom, niveau, filiere)
    VALUES (1, 'INFO-2A', 'Bac+2', 'Informatique')
""")

# Salles
conn.execute("""
    INSERT OR IGNORE INTO salles (id, nom, batiment, raspberry_ip, esp32_ip)
    VALUES (1, 'Salle 101', 'Batiment A', '192.168.137.164.101', '192.168.137.92')
""")

# Profs
conn.execute("""
    INSERT OR IGNORE INTO profs (id, nom, prenom, rfid_uid, matiere)
    VALUES (1, 'RAFIK', 'Mohamed', 'D07FF51B', 'Reseaux')
""")

# Etudiants — mettez les vrais RFID de vos badges
conn.execute("""
    INSERT OR IGNORE INTO etudiants (id, nom, prenom, rfid_uid, classe_id)
    VALUES (1, 'Haji', 'Mohammed', '3AA15124', 1)
""")
conn.execute("""
    INSERT OR IGNORE INTO etudiants (id, nom, prenom, rfid_uid, classe_id)
    VALUES (2, 'Meziani', 'Sara', 'ETU002', 1)
""")

# EDT
conn.execute("DELETE FROM emploi_du_temps")
conn.execute("""
    INSERT INTO emploi_du_temps
        (salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
    VALUES (1, 1, 1, ?, ?, ?, 'Reseaux')
""", (jour, heure_debut, heure_fin))

# Compte gestionnaire
mdp_hash = hashlib.sha256("admin123".encode()).hexdigest()
conn.execute("""
    INSERT OR IGNORE INTO gestionnaire (login, password_hash, nom)
    VALUES ('gestionnaire', ?, 'Mme Administratrice')
""", (mdp_hash,))

conn.commit()
conn.close()
print("Donnees inserees avec succes !")
print("Prof RFID    : PROF001")
print("Etudiant 1   : 3AA15124 (Mohammed Haji)")
print("Etudiant 2   : ETU002 (Sara Meziani)")
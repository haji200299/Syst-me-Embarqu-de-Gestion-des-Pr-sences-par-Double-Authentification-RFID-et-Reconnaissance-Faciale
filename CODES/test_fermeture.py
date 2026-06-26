# test_fermeture.py

from database import get_connection
from datetime import datetime, timedelta

conn = get_connection()

# Créer une séance qui a expiré il y a 5 secondes
maintenant = datetime.now()
debut      = (maintenant - timedelta(minutes=91)).strftime("%Y-%m-%d %H:%M:%S")
fin_prevue = (maintenant - timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")

# Insérer un étudiant de test s'il n'existe pas
conn.execute("""
    INSERT OR IGNORE INTO etudiants (nom, prenom, rfid_uid, classe_id)
    VALUES ('Test', 'Etudiant', 'ETU001', 1)
""")

# Récupérer l'edt_id
edt = conn.execute("SELECT id FROM emploi_du_temps LIMIT 1").fetchone()
if not edt:
    print("Erreur : aucun EDT trouvé. Lancez d'abord test_insert.py")
    conn.close()
    exit()

# Insérer une séance déjà expirée
conn.execute("""
    INSERT INTO seances
        (edt_id, date, heure_debut_reelle, heure_fin_prevue, statut, ouverte_par_rfid)
    VALUES (?, ?, ?, ?, 'ouverte', 'PROF001')
""", (edt["id"], maintenant.strftime("%Y-%m-%d"), debut, fin_prevue))

conn.commit()
conn.close()
print(f"Séance expirée insérée — fin prévue : {fin_prevue}")
print("Attendez 60 secondes maximum et vérifiez les logs du serveur.")
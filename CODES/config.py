# config.py

# ─── Seuils de présence (en minutes) ──────────────────────────────────────────
SEUIL_PRESENT = 3   # 0 à 5 min → présent
SEUIL_RETARD  = 8    # 6 à 20 min → retard
                      # au-delà de 20 min → absent (scan refusé)

# ─── Durée d'une séance (en minutes) ─────────────────────────────────────────
DUREE_SEANCE = 8    # Le système ferme automatiquement après 90 min

# ─── Fenêtre de détection de fraude (en secondes) ────────────────────────────
FENETRE_FRAUDE = 30   # Si RFID A + visage B dans les 30 sec → alerte fraude

# ─── Serveur Flask ─────────────────────────────────────────────────────────────
FLASK_HOST = "0.0.0.0"   # écoute sur toutes les interfaces réseau
FLASK_PORT = 5000         # le Raspberry/ESP32 appellera http://IP_PC:5000/...
FLASK_DEBUG = True        # affiche les erreurs en détail (mettre False en prod)

# ─── Base de données ──────────────────────────────────────────────────────────
DATABASE_PATH = "presence.db"   # fichier SQLite créé dans le dossier du projet
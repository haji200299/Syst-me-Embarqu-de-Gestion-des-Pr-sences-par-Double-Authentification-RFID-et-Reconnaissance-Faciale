# database.py

import sqlite3
from config import DATABASE_PATH


def get_connection():
    """
    Ouvre et retourne une connexion à la base de données.
    row_factory = sqlite3.Row permet d'accéder aux colonnes par leur nom
    (ex: row["nom"]) plutôt que par leur index (row[0]).
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # active les clés étrangères
    return conn


def init_db():
    """
    Crée toutes les tables si elles n'existent pas encore.
    Cette fonction est appelée une seule fois au démarrage du serveur.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── Table : classes ────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nom     TEXT NOT NULL,
            niveau  TEXT NOT NULL,
            filiere TEXT NOT NULL
        )
    """)

    # ── Table : profs ─────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nom      TEXT NOT NULL,
            prenom   TEXT NOT NULL,
            rfid_uid TEXT NOT NULL UNIQUE,  -- badge RFID unique par prof
            matiere  TEXT NOT NULL,
            actif    INTEGER DEFAULT 1      -- 1=actif, 0=désactivé
        )
    """)

    # ── Table : etudiants ────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etudiants (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nom           TEXT NOT NULL,
            prenom        TEXT NOT NULL,
            rfid_uid      TEXT NOT NULL UNIQUE,
            face_encoding BLOB,             -- encodage facial stocké en binaire
            classe_id     INTEGER NOT NULL,
            actif         INTEGER DEFAULT 1,
            FOREIGN KEY (classe_id) REFERENCES classes(id)
        )
    """)

    # ── Table : salles ────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salles (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nom          TEXT NOT NULL,
            batiment     TEXT,
            raspberry_ip TEXT,   -- IP du Raspberry installé dans cette salle
            esp32_ip     TEXT,   -- IP de l'ESP32 installé dans cette salle
            active       INTEGER DEFAULT 1
        )
    """)

    # ── Table : emploi_du_temps ───────────────────────────────────────────────
    # C'est le planning fixe hebdomadaire, organisé par salle.
    # jour_semaine : 0=lundi, 1=mardi, ..., 6=dimanche
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emploi_du_temps (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            salle_id    INTEGER NOT NULL,
            prof_id     INTEGER NOT NULL,
            classe_id   INTEGER NOT NULL,
            jour_semaine INTEGER NOT NULL,  -- 0 à 6
            heure_debut TEXT NOT NULL,      -- format "HH:MM"
            heure_fin   TEXT NOT NULL,      -- format "HH:MM"
            matiere     TEXT NOT NULL,
            FOREIGN KEY (salle_id)  REFERENCES salles(id),
            FOREIGN KEY (prof_id)   REFERENCES profs(id),
            FOREIGN KEY (classe_id) REFERENCES classes(id)
        )
    """)

    # ── Table : seances ───────────────────────────────────────────────────────
    # Instance réelle d'un cours : créée quand le prof bipe, fermée après 90 min.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seances (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            edt_id              INTEGER NOT NULL,
            date                TEXT NOT NULL,         -- "YYYY-MM-DD"
            heure_debut_reelle  TEXT NOT NULL,         -- "YYYY-MM-DD HH:MM:SS"
            heure_fin_prevue    TEXT NOT NULL,         -- debut + 90 min
            heure_fin_reelle    TEXT,                  -- NULL tant que pas fermée
            statut              TEXT DEFAULT 'ouverte', -- 'ouverte' ou 'fermee'
            ouverte_par_rfid    TEXT NOT NULL,         -- UID du badge du prof
            FOREIGN KEY (edt_id) REFERENCES emploi_du_temps(id)
        )
    """)

    # ── Table : presences ────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presences (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id       INTEGER NOT NULL,
            etudiant_id     INTEGER NOT NULL,
            timestamp_scan  TEXT NOT NULL,
            methode         TEXT DEFAULT 'rfid+visage', -- 'rfid+visage' ou 'exceptionnel'
            statut          TEXT NOT NULL,  -- 'present', 'retard', 'absent'
            valide_par_prof INTEGER DEFAULT 0,  -- 1 si validé manuellement
            justification   TEXT,               -- texte libre si absent justifié
            FOREIGN KEY (seance_id)   REFERENCES seances(id),
            FOREIGN KEY (etudiant_id) REFERENCES etudiants(id),
            UNIQUE (seance_id, etudiant_id)  -- un seul enregistrement par étudiant/séance
        )
    """)

    # ── Table : alertes ───────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            seance_id       INTEGER,
            type_alerte     TEXT NOT NULL,  -- 'fraude', 'erreur', 'panne'
            rfid_scanne     TEXT,
            visage_detecte  TEXT,
            description     TEXT,
            timestamp       TEXT NOT NULL,
            traitee         INTEGER DEFAULT 0,  -- 0=non traitée, 1=traitée
            FOREIGN KEY (seance_id) REFERENCES seances(id)
        )
    """)

    # ── Table : gestionnaire ─────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gestionnaire (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            login         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            nom           TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Base de données initialisée avec succès.")
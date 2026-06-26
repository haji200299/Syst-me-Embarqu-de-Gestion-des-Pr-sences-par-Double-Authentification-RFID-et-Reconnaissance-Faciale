# routes/scan_routes.py — version Option A (simplifié)

from flask import Blueprint, request, jsonify
from database import get_connection
from config import SEUIL_PRESENT, SEUIL_RETARD
from datetime import datetime

scan_bp = Blueprint("scan", __name__, url_prefix="/api")


@scan_bp.route("/scan/presence", methods=["POST"])
def enregistrer_presence():
    """
    Appelée uniquement par le Raspberry Pi.
    Le Raspberry a déjà fait la vérification RFID + visage localement.
    Corps attendu :
    {
        "etudiant_id" : 12,
        "salle_id"    : 1,
        "methode"     : "rfid+visage",   # ou "exceptionnel"
        "confiance"   : 0.95             # score reconnaissance faciale
    }
    """
    data = request.get_json()

    champs = ["etudiant_id", "salle_id", "methode"]
    for champ in champs:
        if champ not in data:
            return jsonify({"erreur": f"Champ manquant : {champ}"}), 400

    etudiant_id = data["etudiant_id"]
    salle_id    = data["salle_id"]
    methode     = data["methode"]
    maintenant  = datetime.now()

    conn = get_connection()
    cursor = conn.cursor()

    # ── 1. Vérifier que l'étudiant existe ─────────────────────────────────────
    etudiant = cursor.execute(
        "SELECT * FROM etudiants WHERE id = ? AND actif = 1",
        (etudiant_id,)
    ).fetchone()

    if not etudiant:
        conn.close()
        return jsonify({"statut": "refuse", "message": "Étudiant inconnu"}), 403

    # ── 2. Vérifier qu'une séance est ouverte dans cette salle ────────────────
    seance = cursor.execute("""
        SELECT s.* FROM seances s
        JOIN emploi_du_temps e ON s.edt_id = e.id
        WHERE e.salle_id = ? AND s.statut = 'ouverte'
        LIMIT 1
    """, (salle_id,)).fetchone()

    if not seance:
        conn.close()
        return jsonify({"statut": "refuse", "message": "Aucune séance ouverte"}), 403

    seance_id = seance["id"]
    debut     = datetime.strptime(seance["heure_debut_reelle"], "%Y-%m-%d %H:%M:%S")
    minutes   = (maintenant - debut).total_seconds() / 60

    # ── 3. Vérifier la fenêtre de temps ───────────────────────────────────────
    if minutes > SEUIL_RETARD:
        conn.close()
        return jsonify({
            "statut" : "refuse",
            "message": f"Trop tard — {int(minutes)} min après le début"
        }), 403

    # ── 4. Vérifier si déjà enregistré ────────────────────────────────────────
    deja = cursor.execute("""
        SELECT * FROM presences
        WHERE seance_id = ? AND etudiant_id = ?
    """, (seance_id, etudiant_id)).fetchone()

    if deja:
        conn.close()
        return jsonify({
            "statut" : "deja_enregistre",
            "message": f"{etudiant['prenom']} déjà enregistré(e)"
        }), 200

    # ── 5. Déterminer le statut présent ou retard ──────────────────────────────
    statut = "present" if minutes <= SEUIL_PRESENT else "retard"

    # ── 6. Enregistrer la présence ────────────────────────────────────────────
    # Si methode = "exceptionnel" → valide_par_prof = 0 (attente validation)
    valide = 0 if methode == "exceptionnel" else 0

    cursor.execute("""
        INSERT INTO presences
            (seance_id, etudiant_id, timestamp_scan, methode, statut, valide_par_prof)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (seance_id, etudiant_id,
          maintenant.strftime("%Y-%m-%d %H:%M:%S"),
          methode, statut, valide))

    conn.commit()
    conn.close()

    msg = "Présence enregistrée" if statut == "present" else "Retard enregistré"
    print(f"[PRÉSENCE] {etudiant['prenom']} {etudiant['nom']} → {statut} ({methode})")

    return jsonify({
        "statut" : statut,
        "message": f"{msg} — {etudiant['prenom']} {etudiant['nom']}",
        "nom"    : f"{etudiant['prenom']} {etudiant['nom']}"
    }), 200


@scan_bp.route("/scan/alerte", methods=["POST"])
def signaler_alerte():
    data = request.get_json()

    if not data:
        return jsonify({"statut": "erreur", "message": "Donnees manquantes"}), 400

    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO alertes
                (seance_id, type_alerte, rfid_scanne, visage_detecte, description, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get("seance_id"),
            data.get("type_alerte", "fraude"),
            data.get("rfid_scanne", ""),
            data.get("visage_detecte", ""),
            data.get("description", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
        return jsonify({"statut": "ok", "message": "Alerte enregistree"}), 201

    except Exception as e:
        conn.close()
        print("[ERREUR alerte] " + str(e))
        return jsonify({"statut": "erreur", "message": str(e)}), 500
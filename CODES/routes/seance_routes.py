# routes/seance_routes.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify
from database import get_connection
from config import DUREE_SEANCE
from datetime import datetime, timedelta

# Blueprint = mini-groupe de routes qu'on branche sur l'app principale
seance_bp = Blueprint("seance", __name__, url_prefix="/api")


@seance_bp.route("/seance/ouvrir", methods=["POST"])
def ouvrir_seance():
    data = request.get_json()

    if not data or "rfid_uid" not in data:
        return jsonify({"erreur": "rfid_uid manquant"}), 400

    rfid_uid   = data["rfid_uid"].strip().upper()
    maintenant = datetime.now()

    conn   = get_connection()
    cursor = conn.cursor()

    prof = cursor.execute(
        "SELECT * FROM profs WHERE rfid_uid = ? AND actif = 1",
        (rfid_uid,)
    ).fetchone()

    if not prof:
        print(f"[SEANCE] REFUSE : Badge prof non reconnu -> {rfid_uid}")
        conn.close()
        return jsonify({"statut": "refuse", "message": "Badge prof non reconnu"}), 403

    jour_actuel    = maintenant.weekday()
    heure_actuelle = maintenant.strftime("%H:%M")

    print(f"[SEANCE] Prof trouve : {prof['prenom']} {prof['nom']}")
    print(f"[SEANCE] Recherche EDT : jour={jour_actuel}, heure={heure_actuelle}")

    edt = cursor.execute("""
        SELECT edt.*, s.nom as nom_salle, c.nom as nom_classe
        FROM emploi_du_temps edt
        JOIN salles s  ON edt.salle_id  = s.id
        JOIN classes c ON edt.classe_id = c.id
        WHERE edt.prof_id      = ?
          AND edt.jour_semaine = ?
          AND edt.heure_debut  <= ?
          AND edt.heure_fin    >= ?
    """, (prof["id"], jour_actuel, heure_actuelle, heure_actuelle)).fetchone()

    if not edt:
        # Afficher tous les EDT du prof pour voir pourquoi ca ne matche pas
        tous_edts = cursor.execute("""
            SELECT * FROM emploi_du_temps WHERE prof_id = ?
        """, (prof["id"],)).fetchall()

        print(f"[SEANCE] REFUSE : Aucun cours trouve pour ce prof maintenant")
        print(f"[SEANCE] EDT disponibles pour ce prof :")
        for e in tous_edts:
            print(f"  -> jour={e['jour_semaine']} debut={e['heure_debut']} fin={e['heure_fin']}")

        conn.close()
        return jsonify({
            "statut" : "refuse",
            "message": f"Aucun cours prevu maintenant"
        }), 403

    print(f"[SEANCE] EDT trouve : {edt['matiere']} dans {edt['nom_salle']}")

    seance_existante = cursor.execute("""
        SELECT * FROM seances
        WHERE edt_id = ? AND date = ? AND statut = 'ouverte'
    """, (edt["id"], maintenant.strftime("%Y-%m-%d"))).fetchone()

    if seance_existante:
        print(f"[SEANCE] REFUSE : Seance deja ouverte")
        conn.close()
        return jsonify({
            "statut" : "deja_ouverte",
            "message": "Une seance est deja en cours"
        }), 409

    heure_fin_prevue = (maintenant + timedelta(minutes=DUREE_SEANCE)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO seances
            (edt_id, date, heure_debut_reelle, heure_fin_prevue, statut, ouverte_par_rfid)
        VALUES (?, ?, ?, ?, 'ouverte', ?)
    """, (
        edt["id"],
        maintenant.strftime("%Y-%m-%d"),
        maintenant.strftime("%Y-%m-%d %H:%M:%S"),
        heure_fin_prevue,
        rfid_uid
    ))

    conn.commit()
    seance_id = cursor.lastrowid
    conn.close()

    print(f"[SEANCE] Ouverte ! ID={seance_id} matiere={edt['matiere']}")

    return jsonify({
        "statut"    : "ouverte",
        "seance_id" : seance_id,
        "prof"      : f"{prof['prenom']} {prof['nom']}",
        "classe"    : edt["nom_classe"],
        "salle"     : edt["nom_salle"],
        "matiere"   : edt["matiere"],
        "fin_prevue": heure_fin_prevue,
        "message"   : f"Seance ouverte - {edt['matiere']}"
    }), 200


@seance_bp.route("/seance/statut", methods=["GET"])
def statut_seance():
    """
    Permet au Raspberry et à l'ESP32 de vérifier s'il y a une séance
    ouverte dans leur salle en ce moment.
    Paramètre URL : ?salle_id=3
    """
    salle_id = request.args.get("salle_id")

    if not salle_id:
        return jsonify({"erreur": "salle_id manquant"}), 400

    conn = get_connection()
    seance = conn.execute("""
        SELECT s.*, e.matiere, e.prof_id, e.classe_id
        FROM seances s
        JOIN emploi_du_temps e ON s.edt_id = e.id
        WHERE e.salle_id = ? AND s.statut = 'ouverte'
        ORDER BY s.heure_debut_reelle DESC
        LIMIT 1
    """, (salle_id,)).fetchone()
    conn.close()

    if not seance:
        return jsonify({"statut": "fermee"}), 200

    return jsonify({
        "statut": "ouverte",
        "seance_id": seance["id"],
        "matiere": seance["matiere"],
        "heure_debut": seance["heure_debut_reelle"],
        "heure_fin_prevue": seance["heure_fin_prevue"]
    }), 200

@seance_bp.route("/badge/type", methods=["GET"])
def type_badge():
    rfid_uid = request.args.get("rfid_uid", "").strip().upper()

    if not rfid_uid:
        return jsonify({"erreur": "rfid_uid manquant"}), 400

    conn = get_connection()

    prof = conn.execute(
        "SELECT id FROM profs WHERE rfid_uid = ? AND actif = 1",
        (rfid_uid,)
    ).fetchone()

    if prof:
        conn.close()
        return jsonify({"type": "prof", "prof_id": prof["id"]}), 200

    etu = conn.execute(
        "SELECT id FROM etudiants WHERE rfid_uid = ? AND actif = 1",
        (rfid_uid,)
    ).fetchone()

    conn.close()

    if etu:
        return jsonify({"type": "etudiant", "etudiant_id": etu["id"]}), 200

    return jsonify({"type": "inconnu"}), 404
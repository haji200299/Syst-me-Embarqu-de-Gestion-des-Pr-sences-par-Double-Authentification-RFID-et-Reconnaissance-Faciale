# routes/gestionnaire_routes.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for

from datetime import datetime
import hashlib
from database import get_connection
gest_bp = Blueprint("gestionnaire", __name__)


# ════════════════════════════════════════════════════════
#  AUTHENTIFICATION
# ════════════════════════════════════════════════════════

@gest_bp.route("/")
def index():
    """Page principale — redirige vers login si non connectée."""
    if "gestionnaire" not in session:
        return redirect(url_for("gestionnaire.login"))
    return render_template("index.html")


@gest_bp.route("/login", methods=["GET", "POST"])
def login():
    """Page de connexion."""
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    login_saisi = data.get("login", "").strip()
    mdp_saisi   = data.get("password", "").strip()

    # Hacher le mot de passe en SHA256 pour comparer avec la BDD
    mdp_hash = hashlib.sha256(mdp_saisi.encode()).hexdigest()

    conn = get_connection()
    gest = conn.execute(
        "SELECT * FROM gestionnaire WHERE login = ? AND password_hash = ?",
        (login_saisi, mdp_hash)
    ).fetchone()
    conn.close()

    if not gest:
        return jsonify({"erreur": "Identifiants incorrects"}), 401

    session["gestionnaire"] = gest["nom"]
    return jsonify({"statut": "ok", "nom": gest["nom"]}), 200


@gest_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("gestionnaire.login"))


# ════════════════════════════════════════════════════════
#  TABLEAU DE BORD
# ════════════════════════════════════════════════════════

@gest_bp.route("/api/dashboard")
def dashboard():
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401

    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()

    seances = conn.execute("""
        SELECT s.*, e.matiere, e.heure_debut, e.heure_fin,
               p.nom as prof_nom, p.prenom as prof_prenom,
               c.nom as classe_nom, sa.nom as salle_nom
        FROM seances s
        JOIN emploi_du_temps e ON s.edt_id = e.id
        JOIN profs p           ON e.prof_id = p.id
        JOIN classes c         ON e.classe_id = c.id
        JOIN salles sa         ON e.salle_id = sa.id
        WHERE s.date = ?
        ORDER BY s.heure_debut_reelle
    """, (aujourd_hui,)).fetchall()

    nb_alertes = conn.execute(
        "SELECT COUNT(*) as n FROM alertes WHERE traitee = 0"
    ).fetchone()["n"]

    stats = conn.execute("""
        SELECT
            COUNT(CASE WHEN p.statut = 'present' THEN 1 END) as presents,
            COUNT(CASE WHEN p.statut = 'retard'  THEN 1 END) as retards,
            COUNT(CASE WHEN p.statut = 'absent'  THEN 1 END) as absents
        FROM presences p
        JOIN seances s ON p.seance_id = s.id
        WHERE s.date = ?
    """, (aujourd_hui,)).fetchone()

    conn.close()

    return jsonify({
        "seances"   : [dict(s) for s in seances],
        "nb_alertes": nb_alertes,
        "stats"     : dict(stats)
    }), 200


# ════════════════════════════════════════════════════════
#  PRÉSENCES
# ════════════════════════════════════════════════════════

@gest_bp.route("/api/presences/<int:seance_id>")
def presences_seance(seance_id):
    """Retourne toutes les présences d'une séance donnée."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorisé"}), 401

    conn = get_connection()
    presences = conn.execute("""
        SELECT p.*, e.nom, e.prenom, e.rfid_uid
        FROM presences p
        JOIN etudiants e ON p.etudiant_id = e.id
        WHERE p.seance_id = ?
        ORDER BY e.nom, e.prenom
    """, (seance_id,)).fetchall()
    conn.close()

    return jsonify([dict(p) for p in presences]), 200


@gest_bp.route("/api/presences/<int:presence_id>/modifier", methods=["POST"])
def modifier_presence(presence_id):
    """
    Permet à la gestionnaire de modifier le statut d'une présence.
    Ex: absent → justifié, retard → présent, etc.
    Corps attendu : { "statut": "justifie", "justification": "Certificat médical" }
    """
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorisé"}), 401

    data          = request.get_json()
    nouveau_statut = data.get("statut")
    justification  = data.get("justification", "")

    statuts_valides = ["present", "retard", "absent", "justifie"]
    if nouveau_statut not in statuts_valides:
        return jsonify({"erreur": "Statut invalide"}), 400

    conn = get_connection()
    conn.execute("""
        UPDATE presences
        SET statut = ?, justification = ?, valide_par_prof = 1
        WHERE id = ?
    """, (nouveau_statut, justification, presence_id))
    conn.commit()
    conn.close()

    return jsonify({"statut": "ok", "message": "Présence modifiée"}), 200


# ════════════════════════════════════════════════════════
#  EMPLOI DU TEMPS
# ════════════════════════════════════════════════════════

@gest_bp.route("/api/edt", methods=["GET"])
def get_edt():
    """Retourne tout l'emploi du temps."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorisé"}), 401

    conn = get_connection()
    edt = conn.execute("""
        SELECT e.*,
               p.nom as prof_nom, p.prenom as prof_prenom,
               c.nom as classe_nom,
               s.nom as salle_nom
        FROM emploi_du_temps e
        JOIN profs p   ON e.prof_id   = p.id
        JOIN classes c ON e.classe_id = c.id
        JOIN salles s  ON e.salle_id  = s.id
        ORDER BY e.jour_semaine, e.heure_debut
    """).fetchall()
    conn.close()

    return jsonify([dict(e) for e in edt]), 200


@gest_bp.route("/api/edt/ajouter", methods=["POST"])
def ajouter_edt():
    """
    Ajoute un créneau dans l'EDT.
    Corps : { salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere }
    """
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorisé"}), 401

    data = request.get_json()
    champs = ["salle_id", "prof_id", "classe_id", "jour_semaine",
              "heure_debut", "heure_fin", "matiere"]

    for champ in champs:
        if champ not in data:
            return jsonify({"erreur": f"Champ manquant : {champ}"}), 400

    conn = get_connection()
    conn.execute("""
        INSERT INTO emploi_du_temps
            (salle_id, prof_id, classe_id, jour_semaine, heure_debut, heure_fin, matiere)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data["salle_id"], data["prof_id"], data["classe_id"],
          data["jour_semaine"], data["heure_debut"], data["heure_fin"],
          data["matiere"]))
    conn.commit()
    conn.close()

    return jsonify({"statut": "ok", "message": "Créneau ajouté"}), 201


@gest_bp.route("/api/edt/<int:edt_id>/supprimer", methods=["DELETE"])
def supprimer_edt(edt_id):
    """Supprime un créneau de l'EDT."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorisé"}), 401

    conn = get_connection()
    conn.execute("DELETE FROM emploi_du_temps WHERE id = ?", (edt_id,))
    conn.commit()
    conn.close()

    return jsonify({"statut": "ok", "message": "Créneau supprimé"}), 200


# ════════════════════════════════════════════════════════
#  ALERTES
# ════════════════════════════════════════════════════════

@gest_bp.route("/api/alertes")
def get_alertes():
    """Retourne toutes les alertes non traitées."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorisé"}), 401

    conn = get_connection()
    alertes = conn.execute("""
        SELECT a.*, s.date, e.matiere
        FROM alertes a
        LEFT JOIN seances s           ON a.seance_id = s.id
        LEFT JOIN emploi_du_temps e   ON s.edt_id = e.id
        WHERE a.traitee = 0
        ORDER BY a.timestamp DESC
    """).fetchall()
    conn.close()

    return jsonify([dict(a) for a in alertes]), 200


@gest_bp.route("/api/alertes/<int:alerte_id>/traiter", methods=["POST"])
def traiter_alerte(alerte_id):
    """Marque une alerte comme traitée."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorisé"}), 401

    conn = get_connection()
    conn.execute("UPDATE alertes SET traitee = 1 WHERE id = ?", (alerte_id,))
    conn.commit()
    conn.close()

    return jsonify({"statut": "ok"}), 200


# ════════════════════════════════════════════════════════
#  LISTES (pour remplir les formulaires)
# ════════════════════════════════════════════════════════

@gest_bp.route("/api/listes")
def get_listes():
    """Retourne profs, classes et salles pour alimenter les menus déroulants."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorisé"}), 401

    conn = get_connection()
    profs   = conn.execute("SELECT id, nom, prenom, matiere FROM profs WHERE actif=1").fetchall()
    classes = conn.execute("SELECT id, nom, niveau, filiere FROM classes").fetchall()
    salles  = conn.execute("SELECT id, nom, batiment FROM salles WHERE active=1").fetchall()
    conn.close()

    return jsonify({
        "profs"  : [dict(p) for p in profs],
        "classes": [dict(c) for c in classes],
        "salles" : [dict(s) for s in salles]
    }), 200

@gest_bp.route("/api/dashboard/test")
def dashboard_test():
    """
    Route de test sans authentification.
    A supprimer en production !
    """
    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()

    seances = conn.execute("""
     SELECT s.*, e.matiere, e.heure_debut, e.heure_fin,
           e.id as edt_id,
           p.nom as prof_nom, p.prenom as prof_prenom,
           c.nom as classe_nom, sa.nom as salle_nom
     FROM seances s
     JOIN emploi_du_temps e ON s.edt_id = e.id
     JOIN profs p           ON e.prof_id = p.id
     JOIN classes c         ON e.classe_id = c.id
     JOIN salles sa         ON e.salle_id = sa.id
     WHERE s.date = ?
     ORDER BY s.heure_debut_reelle
    """, (aujourd_hui,)).fetchall()
    
    nb_alertes = conn.execute(
        "SELECT COUNT(*) as n FROM alertes WHERE traitee = 0"
    ).fetchone()["n"]

    stats = conn.execute("""
        SELECT
            COUNT(CASE WHEN p.statut = 'present' THEN 1 END) as presents,
            COUNT(CASE WHEN p.statut = 'retard'  THEN 1 END) as retards,
            COUNT(CASE WHEN p.statut = 'absent'  THEN 1 END) as absents
        FROM presences p
        JOIN seances s ON p.seance_id = s.id
        WHERE s.date = ?
    """, (aujourd_hui,)).fetchone()

    conn.close()

    return jsonify({
        "seances"   : [dict(s) for s in seances],
        "nb_alertes": nb_alertes,
        "stats"     : dict(stats)
    }), 200

# ════════════════════════════════════════════════
#  SALLES ET EDT PAR SALLE
# ════════════════════════════════════════════════

@gest_bp.route("/api/salles")
def get_salles():
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    conn = get_connection()
    salles = conn.execute("SELECT * FROM salles WHERE active = 1").fetchall()
    conn.close()
    return jsonify([dict(s) for s in salles]), 200


@gest_bp.route("/api/salle/<int:salle_id>/edt")
def get_edt_salle(salle_id):
    """EDT complet d'une salle avec historique des seances."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401

    conn = get_connection()
    edt = conn.execute("""
        SELECT e.*,
               p.nom as prof_nom, p.prenom as prof_prenom,
               c.nom as classe_nom
        FROM emploi_du_temps e
        JOIN profs p   ON e.prof_id   = p.id
        JOIN classes c ON e.classe_id = c.id
        WHERE e.salle_id = ?
        ORDER BY e.jour_semaine, e.heure_debut
    """, (salle_id,)).fetchall()
    conn.close()
    return jsonify([dict(e) for e in edt]), 200


@gest_bp.route("/api/edt/<int:edt_id>/historique")
def historique_seances(edt_id):
    """Historique de toutes les seances d'un creneau EDT."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401

    conn = get_connection()
    seances = conn.execute("""
        SELECT s.*,
               COUNT(p.id) as nb_presences,
               SUM(CASE WHEN p.statut = 'present'  THEN 1 ELSE 0 END) as nb_presents,
               SUM(CASE WHEN p.statut = 'retard'   THEN 1 ELSE 0 END) as nb_retards,
               SUM(CASE WHEN p.statut = 'absent'   THEN 1 ELSE 0 END) as nb_absents
        FROM seances s
        LEFT JOIN presences p ON s.id = p.seance_id
        WHERE s.edt_id = ?
        GROUP BY s.id
        ORDER BY s.date DESC
    """, (edt_id,)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in seances]), 200


@gest_bp.route("/api/seance/<int:seance_id>/presences")
def presences_detail(seance_id):
    """Detail des presences d'une seance specifique."""
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401

    conn = get_connection()
    presences = conn.execute("""
        SELECT p.*, e.nom, e.prenom, e.rfid_uid
        FROM presences p
        JOIN etudiants e ON p.etudiant_id = e.id
        WHERE p.seance_id = ?
        ORDER BY e.nom, e.prenom
    """, (seance_id,)).fetchall()
    conn.close()
    return jsonify([dict(p) for p in presences]), 200


# ════════════════════════════════════════════════
#  GESTION ETUDIANTS
# ════════════════════════════════════════════════

@gest_bp.route("/api/etudiants")
def get_etudiants():
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    conn = get_connection()
    etus = conn.execute("""
        SELECT e.*, c.nom as classe_nom
        FROM etudiants e
        JOIN classes c ON e.classe_id = c.id
        ORDER BY e.nom, e.prenom
    """).fetchall()
    conn.close()
    return jsonify([dict(e) for e in etus]), 200


@gest_bp.route("/api/etudiants/ajouter", methods=["POST"])
def ajouter_etudiant():
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    data = request.get_json()
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO etudiants (nom, prenom, rfid_uid, classe_id)
            VALUES (?, ?, ?, ?)
        """, (data["nom"], data["prenom"],
              data["rfid_uid"].strip().upper(), data["classe_id"]))
        conn.commit()
        conn.close()
        return jsonify({"statut": "ok"}), 201
    except Exception as e:
        conn.close()
        return jsonify({"erreur": str(e)}), 400


@gest_bp.route("/api/etudiants/<int:etu_id>/modifier", methods=["POST"])
def modifier_etudiant(etu_id):
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    data = request.get_json()
    conn = get_connection()
    conn.execute("""
        UPDATE etudiants SET nom=?, prenom=?, rfid_uid=?, classe_id=?, actif=?
        WHERE id=?
    """, (data["nom"], data["prenom"],
          data["rfid_uid"].strip().upper(),
          data["classe_id"], data.get("actif", 1), etu_id))
    conn.commit()
    conn.close()
    return jsonify({"statut": "ok"}), 200


# ════════════════════════════════════════════════
#  GESTION PROFS
# ════════════════════════════════════════════════

@gest_bp.route("/api/profs")
def get_profs():
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    conn = get_connection()
    profs = conn.execute("SELECT * FROM profs ORDER BY nom").fetchall()
    conn.close()
    return jsonify([dict(p) for p in profs]), 200


@gest_bp.route("/api/profs/ajouter", methods=["POST"])
def ajouter_prof():
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    data = request.get_json()
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO profs (nom, prenom, rfid_uid, matiere)
            VALUES (?, ?, ?, ?)
        """, (data["nom"], data["prenom"],
              data["rfid_uid"].strip().upper(), data["matiere"]))
        conn.commit()
        conn.close()
        return jsonify({"statut": "ok"}), 201
    except Exception as e:
        conn.close()
        return jsonify({"erreur": str(e)}), 400


@gest_bp.route("/api/profs/<int:prof_id>/modifier", methods=["POST"])
def modifier_prof(prof_id):
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    data = request.get_json()
    conn = get_connection()
    conn.execute("""
        UPDATE profs SET nom=?, prenom=?, rfid_uid=?, matiere=?, actif=?
        WHERE id=?
    """, (data["nom"], data["prenom"],
          data["rfid_uid"].strip().upper(),
          data["matiere"], data.get("actif", 1), prof_id))
    conn.commit()
    conn.close()
    return jsonify({"statut": "ok"}), 200


# ════════════════════════════════════════════════
#  GESTION CLASSES
# ════════════════════════════════════════════════

@gest_bp.route("/api/classes")
def get_classes():
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    conn = get_connection()
    classes = conn.execute("SELECT * FROM classes ORDER BY nom").fetchall()
    conn.close()
    return jsonify([dict(c) for c in classes]), 200


@gest_bp.route("/api/classes/ajouter", methods=["POST"])
def ajouter_classe():
    if "gestionnaire" not in session:
        return jsonify({"erreur": "Non autorise"}), 401
    data = request.get_json()
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO classes (nom, niveau, filiere)
            VALUES (?, ?, ?)
        """, (data["nom"], data["niveau"], data["filiere"]))
        conn.commit()
        conn.close()
        return jsonify({"statut": "ok"}), 201
    except Exception as e:
        conn.close()
        return jsonify({"erreur": str(e)}), 400
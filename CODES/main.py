# app.py — version finale complète

from flask import Flask
from flask_cors import CORS
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from database import init_db
from scheduler import demarrer_scheduler

from routes.scan_routes         import scan_bp
from routes.seance_routes       import seance_bp
from routes.gestionnaire_routes import gest_bp

app = Flask(__name__)
app.secret_key = "presence_system_2026"  # ← nécessaire pour les sessions login
CORS(app)

init_db()
demarrer_scheduler()

app.register_blueprint(scan_bp)
app.register_blueprint(seance_bp)
app.register_blueprint(gest_bp)

@app.route("/ping")
def ping():
    return {"status": "ok", "message": "Serveur opérationnel"}, 200

if __name__ == "__main__":
    print(f"[SERVER] Démarrage sur http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False)
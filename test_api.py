# test_api.py  — à mettre dans le dossier presence_system/

import requests
import json

BASE = "http://localhost:5000"

def test_ouvrir_seance():
    print("\n=== Test : Ouverture de séance par le prof ===")
    reponse = requests.post(f"{BASE}/api/seance/ouvrir", json={"rfid_uid": "PROF001"})
    print(f"Code : {reponse.status_code}")
    print(f"Réponse : {json.dumps(reponse.json(), indent=2, ensure_ascii=False)}")

def test_scan_rfid():
    print("\n=== Test : Scan RFID étudiant ===")
    reponse = requests.post(f"{BASE}/api/scan/rfid", json={
        "rfid_uid": "ETU001",
        "salle_id": 1
    })
    print(f"Code : {reponse.status_code}")
    print(f"Réponse : {json.dumps(reponse.json(), indent=2, ensure_ascii=False)}")

def test_statut_seance():
    print("\n=== Test : Statut de la séance en salle 1 ===")
    reponse = requests.get(f"{BASE}/api/seance/statut?salle_id=1")
    print(f"Code : {reponse.status_code}")
    print(f"Réponse : {json.dumps(reponse.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_ouvrir_seance()
    test_statut_seance()
    test_scan_rfid()
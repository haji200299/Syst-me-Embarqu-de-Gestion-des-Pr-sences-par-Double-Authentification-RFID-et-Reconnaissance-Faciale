# test_scenario.py
import requests
import json
import time

RASP_URL = "http://192.168.137.64:5001"   # IP Raspberry
PC_URL   = "http://localhost:5000"

def afficher(titre, reponse):
    print("\n" + "="*45)
    print(f"  {titre}")
    print("="*45)
    print(f"  Code    : {reponse.status_code}")
    print(f"  Reponse : {json.dumps(reponse.json(), indent=4, ensure_ascii=False)}")

print("\n>>> SCENARIO 1 : Prof ouvre la seance")
rep = requests.post(f"{PC_URL}/api/seance/ouvrir",
                    json={"rfid_uid": "D07FF51B"})
afficher("Ouverture seance par prof", rep)

time.sleep(2)

print("\n>>> SCENARIO 2 : Etudiant present (simuler badge + photo)")
# On simule ce que le Raspberry enverrait au PC
rep = requests.post(f"{PC_URL}/api/scan/presence",
                    json={
                        "etudiant_id": 1,
                        "salle_id"   : 1,
                        "methode"    : "rfid+visage",
                        "confiance"  : 0.92
                    })
afficher("Etudiant 1 - Present", rep)

time.sleep(2)

print("\n>>> SCENARIO 3 : Etudiant deja enregistre")
rep = requests.post(f"{PC_URL}/api/scan/presence",
                    json={
                        "etudiant_id": 1,
                        "salle_id"   : 1,
                        "methode"    : "rfid+visage",
                        "confiance"  : 0.90
                    })
afficher("Etudiant 1 - Deuxieme tentative", rep)

time.sleep(2)

print("\n>>> SCENARIO 4 : Etudiant 2 present")
rep = requests.post(f"{PC_URL}/api/scan/presence",
                    json={
                        "etudiant_id": 2,
                        "salle_id"   : 1,
                        "methode"    : "rfid+visage",
                        "confiance"  : 0.88
                    })
afficher("Etudiant 2 - Present", rep)

time.sleep(2)

print("\n>>> SCENARIO 5 : Fraude detectee")
rep = requests.post(f"{PC_URL}/api/scan/alerte",
                    json={
                        "seance_id"     : None,   # None au lieu de 1
                        "type_alerte"   : "fraude",
                        "rfid_scanne"   : "ETU001",
                        "visage_detecte": "2",
                        "description"   : "Badge ETU001 utilise par etudiant 2"
                    })
afficher("Fraude - Alerte enregistree", rep)

time.sleep(2)

print("\n>>> SCENARIO 6 : Dashboard")
rep = requests.get(f"{PC_URL}/api/dashboard/test")   # /test au lieu de /dashboard
afficher("Dashboard gestionnaire", rep)
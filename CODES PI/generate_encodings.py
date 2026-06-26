import sys
import os

if '__file__' in dir():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
else:
    sys.path.insert(0, os.getcwd())

import face_recognition
import pickle

PHOTOS_DIR     = "photos"
ENCODINGS_PATH = "encodings/encodings.pkl"


def generer_encodages():
    """
    Parcourt le dossier photos/
    Pour chaque sous-dossier (etudiant_id) :
        - lit toutes les photos
        - extrait les encodages faciaux
        - sauvegarde dans encodings.pkl
    Format final : { etudiant_id: [encoding1, encoding2, ...] }
    """
    if not os.path.exists(PHOTOS_DIR):
        print("[GEN] Dossier photos/ introuvable")
        return

    os.makedirs("encodings", exist_ok=True)

    encodages      = {}
    total_photos   = 0
    total_visages  = 0
    total_erreurs  = 0

    for nom_dossier in sorted(os.listdir(PHOTOS_DIR)):
        chemin_dossier = os.path.join(PHOTOS_DIR, nom_dossier)

        if not os.path.isdir(chemin_dossier):
            continue

        try:
            etudiant_id = int(nom_dossier)
        except ValueError:
            print("[GEN] Dossier ignore :", nom_dossier)
            continue

        print("\n[GEN] Traitement etudiant ID " + str(etudiant_id) + "...")
        encodages[etudiant_id] = []

        for nom_fichier in os.listdir(chemin_dossier):
            if not nom_fichier.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            chemin_photo = os.path.join(chemin_dossier, nom_fichier)
            total_photos += 1
            print("  -> " + nom_fichier, end=" ")

            try:
                image     = face_recognition.load_image_file(chemin_photo)
                positions = face_recognition.face_locations(image)

                if not positions:
                    print("[ AUCUN VISAGE ]")
                    total_erreurs += 1
                    continue

                if len(positions) > 1:
                    print("[ PLUSIEURS VISAGES - ignoree ]")
                    total_erreurs += 1
                    continue

                encodage = face_recognition.face_encodings(image, positions)[0]
                encodages[etudiant_id].append(encodage)
                total_visages += 1
                print("[ OK ]")

            except Exception as e:
                print("[ ERREUR : " + str(e) + " ]")
                total_erreurs += 1

        nb = len(encodages[etudiant_id])
        if nb == 0:
            print("[GEN] Aucun encodage valide pour etudiant " + str(etudiant_id))
            del encodages[etudiant_id]
        else:
            print("[GEN] Etudiant " + str(etudiant_id) + " : " + str(nb) + " encodage(s)")

    if not encodages:
        print("\n[GEN] Aucun encodage genere - verifiez vos photos")
        return

    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump(encodages, f)

    print("\n" + "="*40)
    print("[GEN] Termine !")
    print("[GEN] Photos traitees   : " + str(total_photos))
    print("[GEN] Visages encodes   : " + str(total_visages))
    print("[GEN] Erreurs           : " + str(total_erreurs))
    print("[GEN] Etudiants encodes : " + str(len(encodages)))
    print("[GEN] Fichier sauvegarde : " + ENCODINGS_PATH)
    print("="*40)


if __name__ == "__main__":
    generer_encodages()
# Système de Gestion des Présences par Double Authentification RFID et Reconnaissance Faciale

Système embarqué IoT conçu pour automatiser la gestion des présences en milieu académique. Il combine l'identification par badge RFID et la reconnaissance faciale afin de garantir une vérification fiable, rapide et sécurisée contre les fraudes courantes comme le prêt de badge ou l'usurpation d'identité.

## Architecture

Le système repose sur une chaîne de 4 composants matériels coordonnés en temps réel :

| Composant | Rôle |
|---|---|
| **Arduino UNO** | Lecture des badges RFID (module MFRC522), affichage LCD I2C, retour sonore via buzzer |
| **ESP32-CAM** | Capture photo dès détection d'un badge, transmission WiFi vers le Raspberry Pi |
| **Raspberry Pi** | Reconnaissance faciale (`face_handler.py`), vérification de cohérence badge/visage et anti-fraude (`badge_handler.py`), serveur de réception (`app.py`) |
| **Serveur PC (Flask)** | API REST, base de données SQLite, scheduler, interface web d'administration |

```
Arduino → ESP32-CAM → Raspberry Pi → PC (Flask + SQLite)
```

## Fonctionnalités

- **Double authentification** obligatoire (RFID + reconnaissance faciale) pour la présence des étudiants
- **Ouverture de séance simplifiée** pour les enseignants par simple scan de badge
- **Calcul automatique du statut** de présence (présent / retard / absent) selon des seuils configurables
- **Détection automatique de fraude** par incohérence entre badge scanné et visage détecté
- **Fermeture automatique des séances** en fin de créneau avec marquage des absents (APScheduler)
- **Interface web complète** : tableau de bord, emploi du temps par salle, historique des séances, gestion des étudiants/enseignants, traitement des alertes
- **Gestion des cas exceptionnels** (oubli de badge avec validation manuelle par l'enseignant)

## Structure du projet

```
CODES/
├── routes/                  # Endpoints API Flask (séances, scans, gestionnaire)
├── templates/                # Interface web (login + tableau de bord)
├── config.py                  # Paramètres centraux (seuils, IPs, ports)
├── database.py                # Schéma et connexion SQLite
├── main.py                    # Point d'entrée du serveur Flask
├── scheduler.py                # Fermeture automatique des séances
├── setup_final.py              # Initialisation des données (classes, profs, étudiants, EDT)
├── simuler_historique.py        # Génération d'un historique de présences réaliste
├── test_api.py / test_complet.py / test_fermeture.py / test_scenario.py   # Scripts de test
├── presence.db                 # Base de données SQLite
Code_Arduino/                # Firmware Arduino (RFID, LCD, buzzer)
Code_ESP32/                  # Firmware ESP32-CAM (capture photo, WiFi)
Code_Raspberry/              # Traitement embarqué côté Raspberry Pi
├── config.py                  # Paramètres (IP du PC, seuils de confiance faciale)
├── app.py                      # Serveur Flask recevant les requêtes de l'ESP32-CAM
├── face_handler.py              # Chargement des encodages et reconnaissance faciale
├── badge_handler.py             # Logique métier : vérification RFID/visage, anti-fraude
├── generate_encodings.py         # Génération des encodages faciaux à partir des photos
```

## Stack technique

**Backend** : Python, Flask, Flask-CORS, SQLite, APScheduler
**Vision par ordinateur** : OpenCV, face_recognition
**Embarqué** : C++ (Arduino/ESP32), MFRC522, LiquidCrystal I2C, ArduinoJson
**Communication** : API REST, HTTP multipart, Serial/UART, SPI, I2C, WiFi
**Frontend** : HTML, CSS, JavaScript

## Cas d'usage couverts

Présence à l'heure · Retard · Absence automatique · Fraude par badge prêté · Badge inconnu · Oubli de carte avec validation manuelle · Changement de créneau · Séance déjà ouverte · Panne réseau temporaire

## Installation rapide

### Serveur PC

```bash
cd CODES
pip install flask flask-cors apscheduler requests
python main.py
```

### Initialiser les données de test

```bash
python setup_final.py
```

### Accéder à l'interface

```
http://localhost:5000
```

### Firmware Arduino / ESP32-CAM

Ouvrir les fichiers `.ino` correspondants dans l'IDE Arduino, adapter les identifiants WiFi et les adresses IP dans la configuration, puis téléverser sur chaque carte.

### Raspberry Pi

```bash
cd Code_Raspberry
pip install flask face_recognition opencv-python requests numpy
python generate_encodings.py   # génère les encodages faciaux à partir des photos
python app.py                   # démarre le serveur de réception
```

## Auteur

Projet académique — Conception et réalisation d'un système embarqué de gestion des présences par double authentification RFID et reconnaissance faciale.

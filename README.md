# Syst-me-Embarqu-de-Gestion-des-Pr-sences-par-Double-Authentification-RFID-et-Reconnaissance-Faciale

Système embarqué IoT permettant l'automatisation complète de la gestion des présences en milieu académique, combinant l'identification par badge RFID et la reconnaissance faciale pour garantir une vérification fiable et sécurisée contre les fraudes (prêt de badge, usurpation d'identité).
Architecture
Le système repose sur une chaîne de 4 composants matériels coordonnés :

Arduino UNO — Lecture des badges RFID (module MFRC522), affichage LCD I2C et retour sonore via buzzer
ESP32-CAM — Capture photo et transmission WiFi vers le Raspberry Pi
Raspberry Pi — Traitement de la reconnaissance faciale et vérification de cohérence badge/visage
Serveur PC (Flask) — API REST, base de données SQLite et interface web d'administration

Fonctionnalités

Double authentification obligatoire (RFID + reconnaissance faciale) pour chaque présence étudiante
Ouverture de séance simplifiée pour les enseignants (badge seul, sans reconnaissance faciale)
Calcul automatique du statut de présence selon des seuils configurables (présent / retard / absent)
Détection automatique des tentatives de fraude par incohérence badge/visage
Fermeture automatique des séances en fin de créneau avec marquage des absents (APScheduler)
Interface web de gestion : tableau de bord, emploi du temps par salle, historique des séances, gestion des étudiants/enseignants, traitement des alertes
Gestion de cas exceptionnels (oubli de badge, validation manuelle par l'enseignant)

Stack technique
Backend : Python, Flask, SQLite, APScheduler

Vision par ordinateur : OpenCV, face_recognition

Embarqué : C++ (Arduino/ESP32), MFRC522, LiquidCrystal I2C

Communication : REST API, HTTP multipart, Serial/UART, SPI, I2C, WiFi

Frontend : HTML, CSS, JavaScript (interface gestionnaire)
Cas d'usage couverts
Présence à l'heure · Retard · Absence · Fraude par badge prêté · Badge inconnu · Oubli de carte · Changement de créneau · Séance déjà ouverte · Panne réseau

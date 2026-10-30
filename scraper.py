import json
import os
import re
from datetime import datetime, timedelta
import cloudscraper
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIGURATION ---
url_mosttechs = "https://mosttechs.com/free-dice-dreams-rolls/"
url_gamewave = "https://gamewave.fr/dice-dreams/dice-dreams-liens-des-lancers-de-des-gratuits/"
filename = "scrapdicedreams.json"

mois_en_to_num = {
    "january": "01", "jan": "01", "januray": "01",
    "february": "02", "feb": "02", "february ": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12"
}

now = datetime.now()
date_now_str = now.strftime("%d/%m/%Y @ %H:%M")
heure_actuelle_str = now.strftime("%H:%M")
limite_conservation = now - timedelta(days=5)

# --- 1B. INITIALISATION FIREBASE ---
firebase_key_raw = os.environ.get('FIREBASE_KEY')
if not firebase_key_raw:
    raise ValueError("Le secret FIREBASE_KEY est introuvable dans l'environnement.")

if not firebase_admin._apps:
    cred_json = json.loads(firebase_key_raw)
    cred = credentials.Certificate(cred_json)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- 2. CHARGEMENT & NETTOYAGE DE L'HISTORIQUE ---
anciens_liens = {}
if os.path.exists(filename):
    try:
        with open(filename, mode="r", encoding="utf-8") as json_file:
            data_chargee = json.load(json_file)
            if isinstance(data_chargee, list):
                for item in data_chargee:
                    if "lienurl" in item:
                        try:
                            date_objet = datetime.strptime(item.get("date", ""), "%d/%m/%Y")
                            if date_objet >= limite_conservation:
                                anciens_liens[item["lienurl"]] = item
                        except:
                            anciens_liens[item["lienurl"]] = item
    except Exception as e:
        print(f"[Attention] Impossible de lire l'historique JSON : {e}")

# Client anti-bot pour contourner Cloudflare
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

json_data = []
liens_visites_session = set() 
nouveaux_liens_detectes = 0

# =====================================================================
# --- 3A. SCRAPING DE MOSTTECHS ---
# =====================================================================
try:
    response = scraper.get(url_mosttechs, timeout=15)
    status_code = response.status_code
    html_text = response.text
except Exception as e:
    status_code = 500
    html_text = ""
    print(f"[Erreur Mosttechs] Connexion impossible : {e}")

if status_code == 200:
    soup = BeautifulSoup(html_text, "html.parser")
    entry_content = soup.find(class_="entry-content") or soup
    current_date_str = now.strftime("%d/%m/%Y")  
    
    for element in entry_content.find_all(["p", "ul", "ol", "strong"]):
        text = element.get_text().strip().lower()
        
        match_date = re.search(r'(\d{1,2})\s+([a-z]{3,})\s+(\d{4})', text)
        if match_date:
            jour = match_date.group(1).zfill(2)
            nom_mois = match_date.group(2)
            annee = match_date.group(3)
            num_mois = mois_en_to_num.get(nom_mois, "01")
            current_date_str = f"{jour}/{num_mois}/{annee}"
            continue  
            
        try:
            date_section = datetime.strptime(current_date_str, "%d/%m/%Y")
            if date_section < limite_conservation:
                continue
        except:
            pass
        
        links = element.find_all("a", href=True)
        for link in links:
            href = link["href"].strip()
            if href.startswith("/") or any(p in href.lower() for p in ["t.me", "telegram.me", "twitter.com", "facebook.com", "whatsapp", "pinterest", "reddit.com"]):
                continue
                
            keywords = ["dicedreams", "superplay", "t.co", "bit.ly", "d10xl"]
            if any(key in href.lower() for key in keywords):
                if href in liens_visites_session:
                    continue
                liens_visites_session.add(href)
                
                type_recompense = "Rolls gratuits"
                
                if href in anciens_liens:
                    date_premier_scraping_str = anciens_liens[href].get("date_scraping", date_now_str)
                    badge_actuel = ""
                    try:
                        date_premier_scraping = datetime.strptime(date_premier_scraping_str, "%d/%m/%Y @ %H:%M")
                        if now - date_premier_scraping < timedelta(hours=6):
                            badge_actuel = "NEW"
                    except:
                        badge_actuel = anciens_liens[href].get("badge", "")

                    json_data.append({
                        "source": anciens_liens[href].get("source", "mosttechs"),
                        "date_scraping": date_premier_scraping_str, 
                        "date_scraping1": anciens_liens[href].get("date_scraping1", f"{current_date_str} @ {heure_actuelle_str}"),
                        "date": current_date_str,  
                        "heure": anciens_liens[href].get("heure", "00:00"),
                        "recompense": anciens_liens[href].get("recompense", type_recompense), 
                        "lienurl": href,
                        "badge": badge_actuel
                    })
                else:
                    nouveaux_liens_detectes += 1
                    json_data.append({
                        "source": "mosttechs",
                        "date_scraping": date_now_str, 
                        "date_scraping1": f"{current_date_str} @ {heure_actuelle_str}",
                        "date": current_date_str,  
                        "heure": heure_actuelle_str,
                        "recompense": type_recompense, 
                        "lienurl": href,
                        "badge": "NEW" 
                    })
else:
    print(f"[Erreur] Échec de la communication réseau avec Mosttechs (Code {status_code}).")


# =====================================================================
# --- 3B. SCRAPING DE GAMEWAVE ---
# =====================================================================
try:
    response = scraper.get(url_gamewave, timeout=15)
    status_code = response.status_code
    html_text = response.text
except Exception as e:
    status_code = 500
    html_text = ""
    print(f"[Erreur Gamewave] Connexion impossible : {e}")

if status_code == 200:
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Recherche du tableau des liens
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")[1:]  # On ignore l'en-tête (Date et heure | Dés gratuits | Lien quotidien)
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                date_heure_text = cols[0].get_text().strip()  # Format ex: "29/10/2026 à 19:00"
                recompense_text = cols[1].get_text().strip()  # Format ex: "50 Dés gratuits"
                link_tag = cols[2].find("a", href=True)
                
                if link_tag:
                    href = link_tag["href"].strip()
                    
                    # Extraction propre de la date et de l'heure
                    match = re.search(r'(\d{2}/\d{2}/\d{4})\s+à\s+(\d{2}:\d{2})', date_heure_text)
                    if match:
                        current_date_str = match.group(1)
                        heure_str = match.group(2)
                    else:
                        current_date_str = now.strftime("%d/%m/%Y")
                        heure_str = "00:00"
                        
                    # Vérification de la validité de la date
                    try:
                        date_section = datetime.strptime(current_date_str, "%d/%m/%Y")
                        if date_section < limite_conservation:
                            continue
                    except:
                        pass
                        
                    if href in liens_visites_session:
                        continue
                    liens_visites_session.add(href)
                    
                    if href in anciens_liens:
                        date_premier_scraping_str = anciens_liens[href].get("date_scraping", date_now_str)
                        badge_actuel = ""
                        try:
                            date_premier_scraping = datetime.strptime(date_premier_scraping_str, "%d/%m/%Y @ %H:%M")
                            if now - date_premier_scraping < timedelta(hours=6):
                                badge_actuel = "NEW"
                        except:
                            badge_actuel = anciens_liens[href].get("badge", "")

                        json_data.append({
                            "source": anciens_liens[href].get("source", "gamewave"),
                            "date_scraping": date_premier_scraping_str, 
                            "date_scraping1": anciens_liens[href].get("date_scraping1", f"{current_date_str} @ {heure_str}"),
                            "date": current_date_str,  
                            "heure": anciens_liens[href].get("heure", heure_str),
                            "recompense": anciens_liens[href].get("recompense", recompense_text), 
                            "lienurl": href,
                            "badge": badge_actuel
                        })
                    else:
                        nouveaux_liens_detectes += 1
                        json_data.append({
                            "source": "gamewave",
                            "date_scraping": date_now_str, 
"date_scraping1": f"{current_date_str} @ {heure_str}",
"date": current_date_str,
"heure": heure_str,
"recompense": recompense_text,
"lienurl": href,
"badge": "NEW"
})
else:
print(f"[Erreur] Échec de la communication réseau avec Gamewave (Code {status_code}).")

=====================================================================


--- 4. TRAITEMENT FINAL & ENREGISTREMENT ---


=====================================================================

if not json_data and anciens_liens:
json_data = list(anciens_liens.values())

Tri chronologique

def extraire_cle_parution(item):
try:
return datetime.strptime(item.get("date", ""), "%d/%m/%Y").timestamp()
except:
return 0
json_data.sort(key=extraire_cle_parution, reverse=True)

Enregistrement local

with open(filename, mode="w", encoding="utf-8") as json_file:
json.dump(json_data, json_file, indent=4, ensure_ascii=False)
print(f"[Terminé] Fichier Dice Dreams {filename} mis à jour ({len(json_data)} liens valides).")

--- 6. PUSH FIREBASE ---

if nouveaux_liens_detectes > 0:
try:
from firebase_admin import messaging
db.collection("notifications").add({
"title": "🎲 Dice Reward ! 🎁",
"body": "New free spins have just been added !",
"nom_du_jeu": "dice_dreams",
"created_at": firestore.SERVER_TIMESTAMP
})
print("[Firebase] Enregistrement d'historique créé.")
message = messaging.Message(
notification=messaging.Notification(
title="🎲 Dice Reward ! 🎁",
body="New free spins have just been added !"
),
topic="dice_dreams"
)
response = messaging.send(message)
print(f"[Firebase Push] Notification propulsée en direct avec succès ! (ID: {response})")
except Exception as e:
print(f"[Firebase] [Erreur] Impossible d'écrire ou d'envoyer l'alerte push direct : {e}")

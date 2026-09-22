import json
from datetime import datetime
import cloudscraper  # Remplace requests pour contourner le blocage
from bs4 import BeautifulSoup
import re

# 1. URL du site cible
url = "https://gamewave.fr/dice-dreams/dice-dreams-liens-des-lancers-de-des-gratuits/"

# Création d'un scraper qui imite un navigateur Chrome sur Windows
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

try:
    response = scraper.get(url)
    status_code = response.status_code
    html_text = response.text
except Exception as e:
    status_code = 500
    html_text = ""
    print(f"Erreur lors du contournement du blocage : {e}")

if status_code == 200:
    soup = BeautifulSoup(html_text, "html.parser")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Liste qui contiendra nos dictionnaires d'objets JSON
    json_data = []
    
    # 2. Scanner TOUS les liens hypertextes de la page
    all_links = soup.find_all("a", href=True)
    
    for link in all_links:
        href = link["href"]
        
        # Cibler n'importe quel lien contenant dicedreams.com
        if "dicedreams.com" in href:
            # Récupérer le bloc de texte entourant le lien
            parent_text = link.find_parent().get_text(separator=" ").strip() if link.find_parent() else ""
            if len(parent_text) < 15 and link.find_parent().find_parent():
                parent_text = link.find_parent().find_parent().get_text(separator=" ").strip()
            
            clean_text = " ".join(parent_text.split())
            
            # --- EXTRACTION DE LA DATE ---
            date_match = re.search(r'\d{2}/\d{2}/\d{4}', clean_text)
            if date_match:
                date_evenement = date_match.group(0)
            else:
                date_courte_match = re.search(r'\b\d{2}/\d{2}\b', clean_text)
                date_evenement = f"{date_courte_match.group(0)}/{date.today().year}" if date_courte_match else date_du_jour
            
            # --- EXTRACTION DE L'HEURE ---
            # Cherche des formats comme "14:35", "08h15", "9h00"
            heure_match = re.search(r'\b\d{1,2}[h:]\d{2}\b', clean_text, re.IGNORECASE)
            if heure_match:
                # Normalisation du format pour toujours avoir HH:MM (ex: 9h15 devient 09:15)
                heure_brute = heure_match.group(0).lower().replace('h', ':')
                if len(heure_brute.split(':')[0]) == 1:
                    heure_brute = "0" + heure_brute
                heure_evenement = heure_brute
            else:
                heure_evenement = "00:00"  # Valeur par défaut si non spécifiée
            
            # Déterminer la quantité de dés
            des_match = re.search(r'\d+\s*(?:Dés|dés|Rolls|rolls|lancers)', clean_text)
            quantite_des = des_match.group(0) if des_match else "dés"
            quantite_des = quantite_des.replace("Récupérer", "").strip()
            
            # Éviter les doublons de liens
            if not any(item["lienurl"] == href for item in json_data):
                json_data.append({
                    "date_scraping": date_now, 
                    "date": date_evenement, 
                    "heure": heure_evenement,
                    "recompense": type_recompense, 
                    "lienurl": href
                })

    # 3. Écriture du fichier JSON
    filename = "scrapcoinmaster.json"
    
    if not json_data:
        json_data.append({
            "date_scraping": date_now,
            "statut": "VIDE",
            "message": "Aucun lien trouvé sur la page. Vérifiez manuellement le site."
        })
        print("Aucun lien extrait.")
    else:
        print(f"Succès total ! {len(json_data)} liens trouvés et sauvegardés.")

    with open(filename, mode="w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
            
else:
    print(f"Erreur d'accès réseau (Code {status_code}). Le site bloque toujours.")

    # 3. Écriture du fichier JSON au lieu du CSV
    filename = "scrapdicedreams.json"
    
    # Si aucun lien n'a été trouvé, on crée une structure d'erreur propre en JSON
    if not json_data:
        json_data.append({
            "Date Scraping": date_now,
            "Statut": "VIDE",
            "Message": "Aucun lien trouvé sur la page. Vérifiez manuellement le site."
        })
        print("Aucun lien extrait.")
    else:
        print(f"Succès total ! {len(json_data)} liens trouvés et sauvegardés malgré la protection.")

    # Écriture dans le fichier physique
    with open(filename, mode="w", encoding="utf-8") as json_file:
        # indent=4 : Crée des retours à la ligne propres (parfait pour les diffs GitHub)
        # ensure_ascii=False : Conserve les accents français (ex: "Quantité", "Evénement")
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
            
else:
    print(f"Erreur d'accès réseau (Code {status_code}). Le site bloque toujours.")


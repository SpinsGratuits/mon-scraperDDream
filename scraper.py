import csv
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
    
    table_data = []
    
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
            
            # Isoler la date (ex: 19/09/2026)
            date_match = re.search(r'\d{2}/\d{2}/\d{4}', clean_text)
            date_evenement = date_match.group(0) if date_match else "Aujourd'hui"
            
            # Déterminer la quantité de dés
            des_match = re.search(r'\d+\s*(?:Dés|dés|Rolls|rolls|lancers)', clean_text)
            quantite_des = des_match.group(0) if des_match else "50 Dés gratuits"
            quantite_des = quantite_des.replace("Récupérer", "").strip()
            
            # Éviter les doublons
            if not any(row[2] == href for row in table_data):
                table_data.append([date_evenement, quantite_des, href])

    # 3. Écriture forcée du fichier CSV
    with open("scrapdicedreams.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date Scraping", "Date et Heure Événement", "Quantité Dés", "Lien Direct Récompense"])
        
        if table_data:
            for row_data in table_data:
                writer.writerow([date_now, row_data[0], row_data[1], row_data[2]])
            print(f"Succès total ! {len(table_data)} liens trouvés et sauvegardés malgré la protection.")
        else:
            writer.writerow([date_now, "VIDE", "Aucun lien trouvé sur la page", "Vérifiez manuellement le site"])
            print("Aucun lien extrait.")
            
else:
    print(f"Erreur d'accès réseau (Code {status_code}). Le site bloque toujours.")

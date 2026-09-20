import csv
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup
import re

# 1. URL du site cible
url = "https://gamewave.fr/dice-dreams/dice-dreams-liens-des-lancers-de-des-gratuits/"

# Création du scraper pour simuler un humain sur Google Chrome
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

try:
    response = scraper.get(url)
    status_code = response.status_code
    html_text = response.text
except Exception as e:
    status_code = 500
    html_text = ""
    print(f"Erreur de connexion : {e}")

if status_code == 200:
    soup = BeautifulSoup(html_text, "html.parser")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    table_data = []
    
    # 2. On trouve le tableau de la page
    table = soup.find("table")
    
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            
            # Si la ligne contient bien les informations du tableau (Date, Dés, Bouton)
            if len(cells) >= 3:
                date_heure = cells[0].text.strip()
                des_gratuits = cells[1].text.strip()
                
                # Ignorer la ligne d'en-tête descriptive
                if "Date" in date_heure or "Dés" in des_gratuits:
                    continue
                
                # Récupérer le lien, PEU IMPORTE son adresse de départ
                link_tag = cells[2].find("a", href=True)
                if link_tag:
                    lien_recompense = link_tag["href"]
                    
                    # Ignorer uniquement les liens vides ou internes au site
                    if lien_recompense and not lien_recompense.startswith("#"):
                        table_data.append([date_heure, des_gratuits, lien_recompense])
    
    # 3. Écriture forcée du fichier CSV
    with open("scrapdicedreams.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date Scraping", "Date et Heure Événement", "Quantité Dés", "Lien Direct Récompense"])
        
        if table_data:
            for row_data in table_data:
                writer.writerow([date_now, row_data[0], row_data[1], row_data[2]])
            print(f"Succès ! {len(table_data)} liens de récupération ont été extraits et sauvegardés.")
        else:
            writer.writerow([date_now, "VIDE", "La structure du tableau a changé sur le site", "Vérifiez le site"])
            print("Aucun lien extrait après analyse approfondie.")
            
else:
    print(f"Erreur d'accès (Code {status_code}).")

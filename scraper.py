import csv
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. URL du site cible
url = "https://gamewave.fr/dice-dreams/dice-dreams-liens-des-lancers-de-des-gratuits/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Trouver tous les liens hypertextes de la page
    all_links = soup.find_all("a", href=True)
    
    # Filtrer pour ne garder que ceux qui commencent par l'adresse demandée
    target_prefix = "https://rewards.dicedreams.com/?handler=reward&link="
    scraped_links = []
    
    for link in all_links:
        href = link["href"]
        if href.startswith(target_prefix):
            # Éviter les doublons dans la même session de scraping
            if href not in scraped_links:
                scraped_links.append(href)
    
    if scraped_links:
        file_exists = os.path.isfile("data.csv")
        
        # Enregistrement dans le CSV
        with open("scapDiceDream.csv", mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Date Scraping", "Lien Cadeau Dice Dreams"])
            
            for valid_link in scraped_links:
                writer.writerow([date_now, valid_link])
                
        print(f"Succès ! {len(scraped_links)} liens trouvés et sauvegardés.")
    else:
        print("Aucun lien correspondant au préfixe n'a été trouvé sur la page.")
else:
    print(f"Erreur lors de l'accès au site : {response.status_code}")

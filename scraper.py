import csv
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. Lancer la requête sur le site cible
url = "https://example.com"  # Remplacez par le site de votre choix
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    # 2. Extraire la donnée (Exemple : le titre H1 du site)
    title = soup.find("h1").text.strip() if soup.find("h1") else "Non trouvé"
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Préparer le fichier de sauvegarde
    file_exists = os.path.isfile("data.csv")

    # 4. Écrire dans le fichier CSV
    with open("data.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Date", "Titre Extrait"])  # En-tête
        writer.writerow([date_now, title])

    print("Scraping réussi et données enregistrées !")
else:
    print(f"Erreur lors du scraping : {response.status_code}")


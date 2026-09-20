import csv
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. URL du site cible
url = "https://gamewave.fr"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. Trouver TOUS les tableaux de la page pour éviter les erreurs de ciblage
    tables = soup.find_all("table")
    table_data = []
    
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td") # On ne prend que les 'td' (on ignore automatiquement les 'th' d'en-tête)
            
            # Vérifier que la ligne contient bien les 3 colonnes de données
            if len(cells) >= 3:
                date_heure = cells[0].text.strip()
                des_gratuits = cells[1].text.strip()
                
                # Extraire le lien hypertexte dans la 3ème colonne
                link_tag = cells[2].find("a", href=True)
                lien_recompense = link_tag["href"] if link_tag else "Pas de lien"
                
                # Vérifier si c'est un lien de récompense valide
                if "dicedreams.com" in lien_recompense:
                    table_data.append([date_heure, des_gratuits, lien_recompense])

    # 3. Écrire et écraser le fichier CSV avec la table complète
    if table_data:
        with open("data.csv", mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            # En-têtes du fichier CSV de sauvegarde
            writer.writerow(["Date Scraping", "Date et Heure Événement", "Quantité Dés", "Lien Direct Récompense"])
            
            # Écriture des lignes collectées
            for row_data in table_data:
                writer.writerow([date_now, row_data[0], row_data[1], row_data[2]])
                
        print(f"Succès ! {len(table_data)} lignes du tableau ont été extraites et sauvegardées.")
    else:
        print("Erreur : Impossible d'extraire des données valides. Aucun lien correspondant n'a été trouvé.")
else:
    print(f"Erreur lors de l'accès au site : {response.status_code}")

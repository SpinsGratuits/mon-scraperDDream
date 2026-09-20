import csv
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

# 1. URL du site cible
url = "https://gamewave.fr"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    table_data = []
    
    # 2. Scanner TOUS les liens hypertextes de la page sans exception
    all_links = soup.find_all("a", href=True)
    
    for link in all_links:
        href = link["href"]
        
        # Cibler n'importe quel lien contenant dicedreams.com
        if "dicedreams.com" in href:
            # Remonter au bloc parent pour chercher du texte textuel (Date ou quantité de dés)
            parent_text = link.find_parent().get_text(separator=" ").strip() if link.find_parent() else ""
            
            # Si le bloc parent est trop court, on cherche dans la ligne (tr) ou paragraphe (p) supérieur
            if len(parent_text) < 15 and link.find_parent().find_parent():
                parent_text = link.find_parent().find_parent().get_text(separator=" ").strip()
            
            # Nettoyer les espaces superflus et retours à la ligne
            clean_text = " ".join(parent_text.split())
            
            # Tenter d'isoler une date (ex: 19/09/2026) présente dans le texte environnant
            date_match = re.search(r'\d{2}/\d{2}/\d{4}', clean_text)
            date_evenement = date_match.group(0) if date_match else "Date non détectée"
            
            # Déterminer le nombre de dés (souvent écrit "50 Dés" ou "50 lancers")
            des_match = re.search(r'\d+\s*(?:Dés|dés|Rolls|rolls|lancers)', clean_text)
            quantite_des = des_match.group(0) if des_match else "50 Dés gratuits (Standard)"
            
            # Supprimer le mot "Récupérer" s'il s'est glissé dans la détection
            quantite_des = quantite_des.replace("Récupérer", "").strip()
            
            # Ajouter aux données en évitant les doublons stricts de liens
            if not any(row[2] == href for row in table_data):
                table_data.append([date_evenement, quantite_des, href])

    # 3. Écriture forcée du fichier CSV
    with open("data.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date Scraping", "Date et Heure Événement", "Quantité Dés", "Lien Direct Récompense"])
        
        if table_data:
            for row_data in table_data:
                writer.writerow([date_now, row_data[0], row_data[1], row_data[2]])
            print(f"Succès total ! {len(table_data)} liens trouvés et sauvegardés.")
        else:
            # Si le site masque tout aux robots, on écrit au moins une ligne d'erreur pour le voir dans le CSV
            writer.writerow([date_now, "ERREUR", "Le site bloque l'accès au contenu", "Vérifiez les règles de sécurité"])
            print("Aucun lien extrait. Une ligne d'alerte a été écrite dans le fichier.")
            
else:
    print(f"Erreur d'accès réseau : {response.status_code}")

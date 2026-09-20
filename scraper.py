import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://gamewave.fr/dice-dreams/dice-dreams-liens-des-lancers-de-des-gratuits/"

def run_click_scraper():
    collected_links = []
    
    with sync_playwright() as p:
        # 1. Lancer un vrai navigateur en tâche de fond
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="fr-FR"
        )
        page = context.new_page()
        
        try:
            # Ouvrir la page cible
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 2. Analyser le code de la page pour repérer le tableau et les lignes
            html_text = page.content()
            soup = BeautifulSoup(html_text, "html.parser")
            table = soup.find("table")
            
            if table:
                rows = table.find_all("tr")
                # On commence à l'index 1 pour ignorer la ligne d'en-tête (Titres des colonnes)
                for index, row in enumerate(rows[1:], start=1):
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 3:
                        date_heure = cells[0].text.strip()
                        des_gratuits = cells[1].text.strip()
                        
                        # Cibler le bouton/lien "Récupérer" spécifique à cette ligne dans le navigateur
                        # On utilise un sélecteur CSS précis basé sur la position de la ligne (nth-of-type)
                        try:
                            button_selector = f"table tr:nth-of-type({index + 1}) td:nth-of-type(3) a"
                            
                            # Vérifier si l'élément existe bien et est cliquable
                            if page.locator(button_selector).count() > 0:
                                # Préparer l'intercepteur de popup/redirection avant de cliquer
                                with context.expect_page(timeout=5000) as new_page_info:
                                    # Cliquer sur le bouton "Récupérer" comme un humain
                                    page.locator(button_selector).click(modifiers=["Control"]) # Simule un Ctrl+Clic pour ouvrir dans un nouvel onglet sans quitter la page
                                
                                # Récupérer l'adresse URL du nouvel onglet qui vient de s'ouvrir
                                new_page = new_page_info.value
                                target_url = new_page.url
                                new_page.close() # Refermer l'onglet immédiatement
                                
                                # Si l'URL capturée est valide, on l'ajoute
                                if target_url and "dicedreams" in target_url:
                                    collected_links.append([date_heure, des_gratuits, target_url])
                        except Exception as click_error:
                            # Si le clic échoue sur une ligne ou expire, on passe à la suivante sans bloquer le script
                            continue
        except Exception as e:
            print(f"Erreur générale pendant la simulation : {e}")
            
        browser.close()
    return collected_links

# Lancer l'extraction par clics
table_data = run_click_scraper()
date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 3. Écriture finale dans le fichier CSV sauvegardé sur le Cloud
with open("data.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Date Scraping", "Date et Heure Événement", "Quantité Dés", "Lien Direct Récompense"])
    
    if table_data:
        for row_data in table_data:
            writer.writerow([date_now, row_data[0], row_data[1], row_data[2]])
        print(f"Succès absolu ! {len(table_data)} liens réels ont été générés par clic, interceptés et sauvegardés.")
    else:
        writer.writerow([date_now, "ÉCHEC CLIC", "Les boutons n'ont pas généré de redirection de liens", "Vérifiez le site"])
        print("Aucun lien n'a pu être intercepté au clic.")

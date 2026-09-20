import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://gamewave.fr"

def run_scraper():
    with sync_playwright() as p:
        # Lancer un navigateur Chrome virtuel imitant un humain
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="fr-FR"
        )
        page = context.new_page()
        
        try:
            # Ouvrir la page et attendre qu'elle soit totalement chargée
            page.goto(url, wait_until="networkidle", timeout=60000)
            # Simuler un défilement humain pour forcer l'affichage du contenu masqué
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            page.wait_for_timeout(2000)
            
            html_text = page.content()
            status_ok = True
        except Exception as e:
            print(f"Erreur lors de la navigation : {e}")
            html_text = ""
            status_ok = False
            
        browser.close()
        return status_ok, html_text

status_success, html_content = run_scraper()

if status_success and html_content:
    soup = BeautifulSoup(html_content, "html.parser")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    table_data = []
    
    # Trouver tous les liens commençant par l'adresse officielle de récompense
    all_links = soup.find_all("a", href=True)
    target_prefix = "https://rewards.dicedreams.com/"
    
    for link in all_links:
        href = link["href"].strip()
        
        if href.startswith(target_prefix):
            # Tenter d'associer le texte qui entoure le bouton (Date et Dés)
            parent = link.find_parent()
            parent_text = parent.get_text(separator=" ").strip() if parent else ""
            
            # Élargir la recherche si le texte est trop court
            if len(parent_text) < 15 and parent and parent.find_parent():
                parent_text = parent.find_parent().get_text(separator=" ").strip()
                
            clean_text = " ".join(parent_text.split())
            
            # Découpage basique pour nettoyer l'affichage
            clean_text = clean_text.replace("Récupérer", "").strip()
            
            # Éviter d'enregistrer plusieurs fois le même lien
            if not any(row[2] == href for row in table_data):
                table_data.append([date_now, clean_text, href])

    # Écriture dans le fichier CSV
    with open("data.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date Scraping", "Informations Récompense", "Lien Direct Récompense"])
        
        if table_data:
            for row_data in table_data:
                writer.writerow(row_data)
            print(f"Succès total ! {len(table_data)} liens Dice Dreams extraits avec Playwright.")
        else:
            writer.writerow([date_now, "AUCUN LIEN TROUVÉ", "Le site a changé sa structure HTML"])
            print("Aucun lien extrait.")
else:
    print("Échec du scraping : Impossible d'accéder au contenu de la page.")

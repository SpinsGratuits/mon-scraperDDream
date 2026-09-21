import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://gamewave.fr/dice-dreams/dice-dreams-liens-des-lancers-de-des-gratuits/"

def run_fast_scraper():
html_text = ""
with sync_playwright() as p:
# Lancer le navigateur en mode ultra-léger
browser = p.chromium.launch(headless=True)
context = browser.new_context(
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
page = context.new_page()

# Bloquer le contenu lourd pour aller très vite
page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2}", lambda route: route.abort())

try:
# Charger la page avec une limite de 20 secondes max
page.goto(url, wait_until="commit", timeout=20000)
page.wait_for_timeout(3000)
html_text = page.content()
except Exception as e:
print(f"Avertissement Timeout mais continuation : {e}")
try:
html_text = page.content()
except:
pass

browser.close()
return html_text

1. Récupération du HTML
html_content = run_fast_scraper()
date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json_data = []

2. Analyse du code avec BeautifulSoup
if html_content:
soup = BeautifulSoup(html_content, "html.parser")
table = soup.find("table")

if table:
rows = table.find_all("tr")
for row in rows:
cells = row.find_all(["td", "th"])
if len(cells) >= 3:
date_heure = cells[0].text.strip()
des_gratuits = cells[1].text.strip()

if "Date" in date_heure or "Dés" in des_gratuits:
continue

link_tag = cells.find("a", href=True)
lien_recompense = link_tag["href"].strip() if link_tag else ""

# Capturer le lien s'il est valide
if lien_recompense and not lien_recompense.startswith("#") and "dicedreams.fr" not in lien_recompense:
# Structure unitaire en dictionnaire pour le format JSON
json_data.append({
"date_evenement": date_heure,
"quantite_des": des_gratuits,
"lien_recompense": lien_recompense
})

3. Écritures de secours globales si la structure du tableau a échoué
if not json_data and html_content:
all_links = soup.find_all("a", href=True)
for link in all_links:
href = link["href"].strip()
if "dicedreams" in href or "rewards" in href:
json_data.append({
"date_evenement": "Lien Direct",
"quantite_des": "Dés Gratuits",
"lien_recompense": href
})

4. Construction de l'objet final à sauvegarder
output_object = {
"derniere_mise_a_jour": date_now,
"statut": "Succès" if json_data else "Aucune donnée trouvée",
"liens": json_data
}

5. Écriture immédiate du fichier JSON (écrase le précédent)
with open("scrapdicedreams.json", mode="w", encoding="utf-8") as file:
# ensure_ascii=False permet de garder les accents français intacts dans le JSON
# indent=4 permet de rendre le fichier JSON lisible à l'œil humain
json.dump(output_object, file, ensure_ascii=False, indent=4)

print(f"Succès ! {len(json_data)} lignes enregistrées au format JSON.")

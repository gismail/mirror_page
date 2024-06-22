# Importer les modules nécessaires
import threading
import time
import selenium.webdriver as webdriver
import http.server
import socketserver
import requests
import lxml.html
from lxml.html.clean import Cleaner

from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--user-data-dir=C:\\Users\\gourm\\AppData\\Local\\Google\\Chrome\\User Data")
options.add_argument("--profile-directory=Default")

driver = webdriver.Chrome(options=options)


# Définir l'adresse et le port du serveur web
HOST = '192.168.184.59' # A modifier selon votre réseau local
PORT = 8080

# Créer un objet handler pour gérer les requêtes HTTP
handler = http.server.SimpleHTTPRequestHandler

# Créer un objet server pour lancer le serveur web
server = socketserver.TCPServer((HOST, PORT), handler)
cleaner = Cleaner(style=True, links=True, add_nofollow=True,meta=True,
                   page_structure=False, safe_attrs_only=False)
# Définir une fonction qui envoie le contenu de l'onglet actif au serveur web
def send_content():
    # Obtenir le contenu de l'onglet actif
    content = driver.page_source

    # Parsez le contenu avec lxml.html.fromstring
    html_doc = lxml.html.fromstring(content)

    # Utilisez la méthode clean_html pour nettoyer le contenu HTML selon vos critères
    filtered_content = cleaner.clean_html(html_doc)

    # Trouver tous les éléments qui ont l'id "footer"
    footer_elements = filtered_content.xpath("//div[@id='footer-container']")

    # Supprimer ces éléments du document HTML
    for element in footer_elements:
        element.getparent().remove(element)
    # Trouver tous les éléments qui ont la classe 'ch2-dialog ch2-dialog-center'
    dialog_elements = filtered_content.find_class('ch2-settings ch2-settings-scan')
    dialog_elements += filtered_content.find_class('ch2-dialog ch2-dialog-center ')
    # Supprimer ces éléments du document HTML
    for element in dialog_elements:
        element.getparent().remove(element)
    # Utilisez la méthode strip_elements pour supprimer les éléments header du document HTML
    #lxml.etree.strip_elements(filtered_content, 'header')

    # Sérialisez l'objet html nettoyé avec la méthode html.tostring et le paramètre method='html'
    filtered_content = lxml.html.tostring(filtered_content).decode('utf-8')
    
    # Créer ou mettre à jour le fichier HTML avec le contenu
    filename = 'mirror.html'
    with open(filename, 'w') as f:
        f.write(filtered_content)

    # Envoyer une requête HTTP au serveur web pour télécharger le fichier HTML
    url = f'http://{HOST}:{PORT}/{filename}'
    response = requests.put(url, data=filtered_content)

# Définir une fonction qui détecte le changement d'onglet actif et appelle la fonction send_content
def on_tab_change():
    # Obtenir l'identifiant de l'onglet actif
    window_handles = driver.window_handles;
    current_tab = driver.current_window_handle
    if(len(window_handles)>1):
        driver.switch_to.window(window_handles[-1])
    # Vérifier si l'onglet actif a changé depuis la dernière vérification
    current_tab = driver.current_window_handle
    if current_tab != on_tab_change.last_tab:
        # Envoyer le contenu de l'onglet actif au serveur web
        send_content()

        # Mettre à jour l'identifiant de l'onglet actif
        on_tab_change.last_tab = current_tab
    else:
        send_content()
# Initialiser l'identifiant de l'onglet actif avec None
on_tab_change.last_tab = None

# Lancer le serveur web dans un thread séparé
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()

# Boucler indéfiniment en vérifiant le changement d'onglet actif toutes les secondes
while True:
    on_tab_change()
    time.sleep(3)

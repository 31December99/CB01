import logging
import re
import sys
import json
import time
from bs4 import BeautifulSoup
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from network import Network
from database import Database

# LOG
logging.basicConfig(level=logging.INFO)


class Website(Network):

    def __init__(self, dominio: str, genere='indice'):
        super().__init__()

        self.dominio = dominio
        self.genere = genere.lower()
        self.database = Database("cb02.db")
        self.database.connect()
        self.database.create_index_page(table=genere)
        self.generes = {
            # FILM
            "indice": "tutti i links",
            "animazione": "https://cb01.review/category/animazione/",
            "avventura": "https://cb01.review/category/avventura/",
            "azione": "https://cb01.review/category/azione/",
            "biografico": "https://cb01.review/category/biografico/",
            "comico": "https://cb01.review/category/comico/",
            "commedia": "https://cb01.review/category/commedia/",
            "documentario": "https://cb01.review/category/documentario/",
            "drammatico": "https://cb01.review/category/drammatico/",
            "erotico": "https://cb01.review/category/erotico/",
            "fantascienza": "https://cb01.review/category/fantascienza/",
            "fantasy": "https://cb01.review/category/fantasy-fantastico/",
            "gangster": "https://cb01.review/category/gangster/",
            "giallo": "https://cb01.review/category/giallo/",
            "grottesco": "https://cb01.review/category/grottesco/",
            "guerra": "https://cb01.review/category/guerra/",
            "horror": "https://cb01.review/category/horror/",
            "musical": "https://cb01.review/category/musical/",
            "noir": "https://cb01.review/category/noir/",
            "poliziesco": "https://cb01.review/category/poliziesco/",
            "sentimentale": "https://cb01.review/category/sentimentale/",
            "storico": "https://cb01.review/category/storico/",
            "thriller": "https://cb01.review/category/thriller/",
            "western": "https://cb01.review/category/western/",
            # SERIE
            "s_animazione": "https://cb01.review/serietv/category/animazione/",

        }

        if self.genere in self.generes:
            self.serie_url = self.generes[self.genere]
        else:
            print("Sezione non trovata !\n")
            print("Sezioni disponibili: ")
            for sezione, link in self.generes.items():
                print(sezione)
            sys.exit()

    @staticmethod
    def replace_dom(url_list: list, nuovo_dominio: str) -> list:
        return [page_url.replace(re.search(r'\.(.+?)\/', page_url).group(1), nuovo_dominio)
                for page_url in url_list]

    def get_video_urls(self, url: str) -> str:

        # ...................................................................
        # Aggiorno il dominio con quello nuovo
        # ...................................................................

        self.driver.get(self.replace_dom(url_list=[url], nuovo_dominio=self.dominio)[0])
        # ...................................................................
        # cerca l'attributo class "ignore-css" ove sono elencati i link
        # ...................................................................
        link_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.ignore-css a')

        # ...................................................................
        # itera su tutti gli elementi e stampa il valore dell'attributo href
        # di ogni link
        # ...................................................................
        stayonline = [link_element.get_attribute('href') for link_element in link_elements if
                      link_element.get_attribute('href') and 'stayonline.pro' in link_element.get_attribute('href')]

        # ...................................................................
        # Prova tutti i link a disposizione nella home del video che hanno
        # come dominio stayonline ( di solito url di mixdrop e maxstream).
        # todo: eventualità che la pubblicità copri la pagina..
        # ...................................................................
        sucess = False
        for player_url in stayonline:
            logging.info(f" stayonline ->  {player_url}")
            self.driver.get(player_url)
            time.sleep(5)

            # ...................................................................
            # Trova il pulsante "Click to Continue"
            # ...................................................................
            button = self.driver.find_element(By.XPATH, '//button[text()="Click to continue"]')

            # ...................................................................
            # Clicca sul pulsante utilizzando JavaScript
            # In quanto ci sono alcuni elementi che si sovrappongono questo
            # dovrebbe "bypassarli..."
            # ...................................................................
            self.driver.execute_script("arguments[0].click();", button)

            # ...................................................................
            # Attendo che sia caricato il player r quindi l'elemento che include
            # il link del video
            # ...................................................................
            try:
                element_present = ec.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div/div[3]/div"
                                                                            "/textarea"))
                WebDriverWait(self.driver, 10).until(element_present)
                sucess = True
                break
            except (TimeoutException, UnexpectedAlertPresentException, WebDriverException):
                logging.info("[Xpath] Provo con link alternativo")
            except (WebDriverException, ConnectionResetError) as e:
                # todo: per il momento riprova va avanti
                logging.info(f"[Webdriver] {e} Attendi 60 secondi. Segnalare home?")
                time.sleep(60)

        # ...................................................................
        # Nessun link ha avuto successo , passo al prossimo video
        # ...................................................................
        if not sucess:
            logging.info("[Xpath] Nessun link ha avuto successo. Passo al prossimo video")
            return 'nessun video'

        # ...................................................................
        # Inizio estrapolazione dati dalla pagine del video per catalogare
        # il link diretto
        # ...................................................................
        pagina_corrente = self.driver.page_source

        # ...................................................................
        # Esegui il parsing della pagina corrente
        # ...................................................................
        soup = BeautifulSoup(pagina_corrente, 'html.parser')

        # ...................................................................
        # Cerco il link del video dentro la pagina
        # ...................................................................
        mixdrop = soup.find(string=re.compile('src="//mixdrop.club/'))
        match = re.search(r'(?<=src=["\'])[^"\']+(?=["\'])', mixdrop)

        # ...................................................................
        # estrai il valore dell'attributo src, se presente
        # ...................................................................
        if match is not None:
            video_url = match.group(0)

            # ...................................................................
            # ottengo il link al download dal link del video
            # aggiorno dominio in 'co'
            # aggiungo "?download"
            # scambio '/f/' con '/d/'
            # ...................................................................
            download_url = self.replace_dom(url_list=[video_url], nuovo_dominio='co')[0]
            download_url = f"https:{download_url}?download"
            download_url = download_url.replace('/e/', '/f/')  # rivedere !
            logging.info(f"Pagina Download: {download_url} ")

            # ...................................................................
            # salvo tutto nel database
            # ...................................................................
            self.database.update_video_url(table=self.genere, url=url, video_url=f"https:{video_url}",
                                           download_url=download_url)
            return video_url

    def get_video_serie_urls(self, url: str) -> str:

        # ...................................................................
        # Aggiorno il dominio con quello nuovo
        # ...................................................................
        self.driver.get(self.replace_dom(url_list=[url], nuovo_dominio='review')[0])

        # ...................................................................
        # Punta alla class div che "contiene" i video in ita e non in sub
        # ...................................................................
        try:
            sp_head = self.driver.find_element(By.XPATH, "/html/body/main/div[2]/div/div[1]/article/div[1]/table["
                                                         "1]/tbody/tr/td/div[2]")
            sp_body = sp_head.find_element(By.CLASS_NAME, "sp-body")

            # todo: cerca la serie in upload solo su Mixdrop
            # todo: occorre identicare anche maxstream
            mixdrop_links = sp_body.find_elements(By.LINK_TEXT, "Mixdrop")
        except NoSuchElementException:
            mixdrop_links = self.driver.find_elements(By.LINK_TEXT, "Mixdrop")

        # ...................................................................
        # contiene un elenco di tutti gli episodi
        # ...................................................................
        if mixdrop_links:
            mixdrop_links = [link.get_attribute("href") for link in mixdrop_links if mixdrop_links]
        else:
            return 'Per questo titolo non ho trovato un upload Mixdrop'
        sucess = False

        for player_url in mixdrop_links:
            self.driver.get(player_url)
            time.sleep(5)
            # ...................................................................
            # Trova il pulsante "Click to Continue"
            # ...................................................................
            button = self.driver.find_element(By.XPATH, '//button[text()="Click to continue"]')

            # ...................................................................
            # Clicca sul pulsante utilizzando JavaScript
            # In quanto ci sono alcuni elementi che si sovrappongono questo dovrebbe "bypassarli..."
            # ...................................................................
            self.driver.execute_script("arguments[0].click();", button)

            # ...................................................................
            # Attendo che sia caricato il player r quindi l'elemento che include
            # il link del video
            # ...................................................................
            try:
                element_present = ec.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div/div[3]/div"
                                                                            "/textarea"))
                WebDriverWait(self.driver, 10).until(element_present)
                sucess = True
            except (TimeoutException, UnexpectedAlertPresentException, WebDriverException):
                logging.info("[Xpath] Provo con link alternativo")
            except (WebDriverException, ConnectionResetError) as e:
                logging.info(f"[Webdriver] {e} Attendi 60 secondi. Segnalare home?")
                time.sleep(60)
                # per il momento riprova va avanti

            # ...................................................................
            # Nessun link ha avuto successo , passo al prossimo video
            # ...................................................................
            if not sucess:
                logging.info("[Xpath] Nessun link ha avuto successo. Passo al prossimo video")
                continue

            # ...................................................................
            # Inizio estrapolazione dati dalla pagine del video per catalogare
            # il link diretto
            # ...................................................................
            pagina_corrente = self.driver.page_source

            # ...................................................................
            # Esegue il parsing della pagina corrente
            # ...................................................................
            soup = BeautifulSoup(pagina_corrente, 'html.parser')

            # ...................................................................
            # Cerco il link del video dentro la pagina
            # ...................................................................
            mixdrop = soup.find(string=re.compile('src="//mixdrop.club/'))
            match = re.search(r'(?<=src=["\'])[^"\']+(?=["\'])', mixdrop)

            # ...................................................................
            # estrai il valore dell'attributo src, se presente
            # ...................................................................
            if match is not None:
                link = match.group(0)
                video_url = self.database.load_video_serie_urls(table=self.genere, urls=url, id_start=0)
                if video_url:
                    video_url = f"{video_url}#{link}"
                else:
                    video_url = f"{link}#"

                logging.info(f"Seguo {player_url} -> Player link https:{link}")
                self.database.update_video_url(table=self.genere, url=url, video_url=video_url)

    def get_genres_titles(self, page: int, nuovo_dominio: str, categoria: str) -> bool:

        """
        :param page: numero di pagina
        :param nuovo_dominio: dominio attivo in questo momento
        :param categoria: categoria di video scelta dal sito
        :return: true se ci sono nuovi titoli false se non ci sono oppure sono già presenti nel database
        """

        self.get(f"{self.serie_url}/page/{page}/")
        time.sleep(4)

        # ...................................................................
        # ottengo tutti gli urls dei video contenuti nella pagina
        # ...................................................................
        card_elements = self.driver.find_elements(By.CLASS_NAME, "card-content")
        links = [card.find_element(By.CLASS_NAME, "card-title").find_element(By.XPATH, ".//a").get_attribute("href")
                 for card in card_elements]

        # ...................................................................
        # Inserisco nel DB tutti i links video se non già presenti
        # ...................................................................
        if links:
            new_titles = [url for url in links if self.database.insert_index(self.genere, url,
                                                                             nuovo_dominio, str(page), categoria)]

            # ...................................................................
            # faccio commit solo se l'elenco non è vuoto
            # ...................................................................
            if new_titles:
                for t in new_titles:
                    logging.info(f"[{self.genere}] Aggiunto nuovo titolo nel DB -> {t}")
                self.database.db.commit()
            return True

    def get_video_urls_download(self, video_url: str) -> bool:

        # Cambio dominio da 'club' a 'co'
        # '/f/' è obbligatorio al posto di '/d/' o altro esempio : https://mixdrop.co/f/84w1wg1xhw1dn?download
        # aggiungere "?download"

        download_url = self.replace_dom(url_list=[video_url], nuovo_dominio='co')[0]
        download_url = f"{download_url}?download"
        download_url = download_url.replace('/e/', '/f/')  # rivedere !
        logging.info(f"Pagina Download: {download_url} ")
        # una volta creato il link. Accedo alla pagina
        self.driver.get(download_url)
        # Attendo che il pulsante di download sia presente
        # Nota: il link potrebbe non essere più valido
        try:
            element_present = ec.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div/div[1]"
                                                                        "/div/div[2]/div/a"))
            WebDriverWait(self.driver, 10).until(element_present)
        except (TimeoutException, UnexpectedAlertPresentException, WebDriverException):
            logging.info("Timeout su ricerca pulsante download. Il link è ancora valido ?")
            return False

        # Lo clicco una volta
        button = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div[1]/div/div[2]/div/a")
        self.driver.execute_script("arguments[0].click();", button)
        # Attendo 3 secondi come da conteggio visualizzato sul corpo del pulsane nella pagina del browser
        time.sleep(4)
        # Attendo 2 secondi come pausa
        time.sleep(3)

        # Clicco nuovamente . Dovrebbe partire il download
        button = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div[1]/div/div[2]/div/a")
        self.driver.execute_script("arguments[0].click();", button)
        # Cerco il link delivery46 nel log e lo memorizzo
        logs = self.driver.get_log("performance")

        if not logs:
            print("*** LOG VUOTO ***")
            self.driver.quit()
            return False

        for log in logs:
            message = json.loads(log["message"])["message"]
            if "Network.responseReceived" == message["method"]:
                url = message['params']['response']['url']
                if 'delivery' in url:
                    logging.info(f"Link diretto: {url}")
                    # self.database.update_download_url(table="indice", video_url=video_url, download_url=url)
                    return url

    def get_index(self):

        movie_index = [
            "https://cb01.dominio/category/animazione",
            "https://cb01.dominio/category/avventura",
            "https://cb01.dominio/category/azione",
            "https://cb01.dominio/category/biografico",
            "https://cb01.dominio/category/comico",
            "https://cb01.dominio/category/commedia",
            "https://cb01.dominio/category/documentario",
            "https://cb01.dominio/category/drammatico",
            "https://cb01.dominio/category/erotico",
            "https://cb01.dominio/category/fantascienza",
            "https://cb01.dominio/category/fantasy-fantastico",
            "https://cb01.dominio/category/gangster",
            "https://cb01.dominio/category/giallo",
            "https://cb01.dominio/category/grottesco",
            "https://cb01.dominio/category/guerra",
            "https://cb01.dominio/category/horror",
            "https://cb01.dominio/category/musical",
            "https://cb01.dominio/category/noir",
            "https://cb01.dominio/category/poliziesco",
            "https://cb01.dominio/category/sentimentale",
            "https://cb01.dominio/category/storico",
            "https://cb01.dominio/category/thriller",
            "https://cb01.dominio/category/western",  # 23
        ]

        serie_index = [

            "https://cb01.dominio/serietv/category/animazione",
            "https://cb01.dominio/serietv/category/avventura",
            "https://cb01.dominio/serietv/category/azione",
            "https://cb01.dominio/serietv/category/biografico",
            "https://cb01.dominio/serietv/category/comico",
            "https://cb01.dominio/serietv/category/commedia",
            "https://cb01.dominio/serietv/category/documentario",
            "https://cb01.dominio/serietv/category/drammatico",
            "https://cb01.dominio/serietv/category/erotico",
            "https://cb01.dominio/serietv/category/fantascienza",
            "https://cb01.dominio/serietv/category/fantasy-fantastico",
            "https://cb01.dominio/serietv/category/gangster",
            "https://cb01.dominio/serietv/category/giallo",
            "https://cb01.dominio/serietv/category/grottesco",
            "https://cb01.dominio/serietv/category/guerra",
            "https://cb01.dominio/serietv/category/horror",
            "https://cb01.dominio/serietv/category/musical",
            "https://cb01.dominio/serietv/category/noir",
            "https://cb01.dominio/serietv/category/poliziesco",
            "https://cb01.dominio/serietv/category/sentimentale",
            "https://cb01.dominio/serietv/category/storico",
            "https://cb01.dominio/serietv/category/thriller",
            "https://cb01.dominio/serietv/category/western",

        ]

        movie_pages = [categoria_link.replace(re.search(r'\.(.+?)\/', categoria_link).group(1), self.dominio)
                       for categoria_link in movie_index]

        series_pages = [categoria_link.replace(re.search(r'\.(.+?)\/', categoria_link).group(1), self.dominio)
                        for categoria_link in serie_index]

        for categoria in movie_pages:
            self.serie_url = categoria
            print(categoria)
            for page in range(1, 200):  # max 200 pagine
                if not self.get_genres_titles(page=page, nuovo_dominio=self.dominio, categoria=categoria):
                    break

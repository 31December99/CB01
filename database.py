import re
import sqlite3
import logging


# LOG
logging.basicConfig(level=logging.INFO)


class Database:

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.db = None

    def connect(self):
        self.db = sqlite3.connect(self.file_name)
        return self.db

    def insert(self, table: str, title: str, section: str, season: str, episode: str, download_url: str, status: str):
        if not download_url:
            return False
        try:
            self.db.execute(f"INSERT INTO {table} (title,section,season,episode,download_url,status)"
                            f" VALUES (?,?,?,?,?,?)",
                            (title, section, season, episode, download_url, status))
        except sqlite3.IntegrityError:
            print(f"l'url del titolo '{title}' è gia stato registrato nel database")

    def insert_index(self, table: str, url: str, nuovo_dominio: str, page: str, categoria: str) -> bool:

        # verifico che sia almeno HD
        """
        if '-hd-' not in url.lower(): # non esiste -hd- nel link serie
            return False
        """

        # verifico che non sia un SUB
        if '-sub-' in url.lower():
            return False

        # Ottengo titolo dal link
        title_tmp = url.replace(f'https://cb01.{nuovo_dominio}/', '')
        title_tmp = title_tmp.replace('/', '')
        title = title_tmp.replace('-', ' ')
        try:
            self.db.execute(f"INSERT INTO {table} (categoria,pagina,title,urls) VALUES (?,?,?,?)",
                            (categoria, page, title, url,))
            return True
        except sqlite3.IntegrityError:
            # print(f"INSERT INDEX: {w} ")
            # print(f"l'url {url} è gia stato registrato nel database")
            return False

    def create_table_page(self, table: str):

        page_table = f"""CREATE TABLE IF NOT EXISTS {table} (
                        id             INTEGER PRIMARY KEY AUTOINCREMENT
                                               UNIQUE
                                               NOT NULL,
                        title       TEXT,
                        section     TEXT,
                        season      TEXT,
                        episode     TEXT, 
                        download_url TEXT,
                        status      TEXT,
                        UNIQUE(download_url) ON CONFLICT FAIL                                              
                    );"""

        self.db.execute(page_table)

    def create_index_page(self, table: str):

        page_table = f"""CREATE TABLE IF NOT EXISTS {table} (
                        id             INTEGER PRIMARY KEY AUTOINCREMENT
                                               UNIQUE
                                               NOT NULL,
                        categoria  TEXT,
                        pagina     TEXT,
                        title      TEXT,
                        urls       TEXT,
                        video_url  TEXT,
                        download_url TEXT,
                        UNIQUE(urls) ON CONFLICT FAIL
                    );"""

        self.db.execute(page_table)

    def load_index(self, table: str, nuovo_dominio: str, id_start: int):
        cursor = self.db.execute(f"SELECT urls FROM {table} WHERE id>?", (id_start,))

        # ....................................................
        # Creo un elenco con tutti i link precedentemente
        # estratti dalle pagine del sito ed eventualmente
        # aggiorno il dominio
        # ....................................................
        return [download_url[0].replace(re.search(r'\.(.+?)\/', download_url[0]).group(1), nuovo_dominio)
                for download_url in cursor.fetchall()]

    def load_last_index(self, table: str) -> int:

        cursor = self.db.execute(f"SELECT id FROM {table} ORDER BY id DESC LIMIT 1")
        return cursor.fetchone()[0]

    def load_video_urls(self, table: str, id_start: int) -> list:

        try:
            cursor = self.db.execute(f"SELECT video_url FROM {table} WHERE id>?", (id_start,))
            return [video_url for video_url in cursor.fetchall()]
        except sqlite3.OperationalError:
            logging.info(" Questa categoria non esiste nel database.")
            return []

    def load_video_serie_urls(self, table: str, urls: str, id_start: int) -> list:
        try:
            cursor = self.db.execute(f"SELECT video_url FROM {table} WHERE urls=? and id>?", (urls, id_start,))
            return cursor.fetchone()[0]
        except sqlite3.OperationalError:
            logging.info(" Questa categoria non esiste nel database.")
            return []

    def update_video_url(self, table: str, url: str, video_url: str, download_url: str):
        self.db.execute(f"UPDATE {table} SET video_url=?,download_url=? WHERE urls=?", (video_url, download_url, url,))
        self.db.commit()

    def update_download_url(self, table: str, video_url: str, download_url: str):
        print(table, video_url, download_url)
        # sospeso
        self.db.execute(f"UPDATE {table} SET download_url=? WHERE video_url LIKE '%' || ? || '%'",
                        (download_url, video_url,))
        self.db.commit()

    def close(self):
        self.db.close()

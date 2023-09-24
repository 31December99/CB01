#!/usr/bin/env python3.9

import argparse
import asyncio
import logging
from web import Website

# LOG
logging.basicConfig(level=logging.INFO)
dominio = "observer"


class Cb01bot:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def start(self):

        parser = argparse.ArgumentParser(description='CB01 downloader', add_help=False)
        parser.add_argument('-all', '--all', action='store_true', help='crea un indice di tutto..')
        parser.add_argument('-movie', '--movie', action='store_true',
                            help='Aggiorna la tabella con gli urls dei movies')
        parser.add_argument('-serie', '--serie', action='store_true',
                            help='Aggiorna la tabella con gli urls delle serie')
        """
        parser.add_argument('-dwmovie', '--dwmovie', action='store_true',
                            help='Aggiorna la tabella Urls per il titolo specificato')
        """
        args = parser.parse_args()

        # ..................................................................
        # Aggiorna la tabella indice con i link di ogni pagina per ogni
        # categoria
        # ..................................................................
        if args.all:
            website = Website(dominio=dominio)
            website.get_index()

        # ..................................................................
        # Aggiorna la tabella indice con i link diretti al player
        # ..................................................................
        if args.movie:
            website = Website(dominio=dominio)
            videos_home = website.database.load_index(table='indice', nuovo_dominio=dominio, id_start=0)
            for home in videos_home:
                logging.info(f" Ho trovato https:{website.get_video_urls(home)}")
                print("- ok -")

        # ..................................................................
        # Cerco di ottenere il link diretto al download
        # ..................................................................
        if args.dwmovie:
            website = Website(dominio=dominio)
            videos_home = website.database.load_video_urls(table='indice', id_start=0)
            for videoUrl in videos_home:
                logging.info(f"Player: {videoUrl[0]}")
                if not website.get_video_urls_download(videoUrl[0]):
                    website.driver.quit()
                    break


if __name__ == "__main__":
    cb01bot = Cb01bot()
    cb01bot.start()

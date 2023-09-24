import random
import logging
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager

# LOG
logging.basicConfig(level=logging.INFO)


class Network:

    @property
    def agent(self):
        uastrings = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 "
            "Safari/537.36",
            "Lynx: Lynx/2.8.8pre.4 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.12.23",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 "
            "Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 "
            "Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 "
            "Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 "
            "Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 "
            "Safari/605.1.15",
            "Samsung Phone: Mozilla/5.0 (Linux; Android 6.0.1; SAMSUNG SM-G570Y Build/MMB29K) AppleWebKit/537.36 ("
            "KHTML,"
            "like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36",
            "like Gecko) Version/10.0 Mobile/14E304 Safari/602.1",
            "Apple iPad: Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) "
            "Version/8.0 Mobile/12H321 Safari/600.1.4",
        ]
        return random.choice(uastrings)

    def __init__(self):
        opts = uc.ChromeOptions()
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--profile-directory=Profile 2")
        opts.add_argument("--user-data-dir=/home/midnight/.config/gtorrents/")

        # opts.add_argument('--headless')
        # opts.add_argument('--disable-gpu')
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument(f"--user-agent={self.agent}")
        opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        self.driver_exec_path = ChromeDriverManager().install()
        self.driver = uc.Chrome(
            driver_executable_path=self.driver_exec_path, options=opts
        )

    def close(self):
        self.driver.quit()

    def get(self, url: str):
        """
        ottengo la pagina
        :return:
        """
        self.driver.get(url)
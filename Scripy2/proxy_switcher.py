import time
import config
import requests
from random import random
from bs4 import BeautifulSoup


def Handler_bad_case(func):
    def error(*args, **kwargs):
        self = args[0]
        while True:
            try:
                return func(*args, **kwargs)
            except AttributeError:
                self.set_new_proxy()
            except Exception:
                time.sleep(10 * random())
                continue

    return error


class Switcher(object):
    def __init__(self):
        self.proxies = []
        self.session = requests.Session()
        self.last_page = None

    @Handler_bad_case
    def send_request(self, endpoint='/'):

        self.session.headers.update({'Connection': 'close',
                                     'Accept': '*/*',
                                     'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                     'Cookie': '$Version=1',
                                     'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
                                     'User-Agent': config.USER_AGENT[0]})
        try:
            response = self.session.get(config.PROXY_URL + endpoint)
        except Exception as e:
            return False

        if response.status_code == 200:
            self.last_page = response.text
            return True
        else:
            if response.status_code == 429:
                sleep_minutes = 5
                time.sleep(sleep_minutes * 60)
                self.send_request()
            else:
                return False

    @Handler_bad_case
    def load_proxies(self):
        html = BeautifulSoup(self.last_page, 'html.parser')
        table = html.find('table', {'id': 'proxylisttable'}).find('tbody')
        rows = ""
        if table is not None:
            rows = table.find_all('tr')
        else:
            return False
        for i in rows:
            tds = i.find_all('td')
            if not tds:
                continue
            ip = tds[0].text
            port = tds[1].text
            self.proxies.append(ip + ':' + port)
        self.proxies = self.proxies[::-1]
        return True

    @Handler_bad_case
    def get_new_proxy(self):
        try:
            return self.proxies.pop()
        except IndexError:
            time.sleep(60 * 1)
            ret = self.send_request()
            if ret:
                self.load_proxies()
                self.get_new_proxy()

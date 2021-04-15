import json
import time
import io
from random import random, choice
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import ProxyError, SSLError

import config
from proxy_switcher import Switcher
Json = []


class Captcha(Exception):
    pass


def Handler_bad_case(func):
    def error(*args, **kwargs):
        self = args[0]
        while True:
            try:
                return func(*args, **kwargs)
            except Captcha:
                self.user_agent = choice(config.USER_AGENT)
                self.set_new_proxy()
            except (ProxyError, SSLError):
                self.set_new_proxy()
    return error


def get_full_url(url):
    if 'http' or 'http' not in url:
        url = config.START_URL + url
    if url.find('?') != -1:
        url = url[:url.find('?')]
    return url


class Scraper(object):
    def __init__(self):
        self.LastPage = None
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=1))
        self.proxy_switcher = Switcher()
        self.user_agent = choice(config.USER_AGENT)
        self.session.proxies = None
        self.set_new_proxy()

    @Handler_bad_case
    def get_page(self, price_max, page=1):
        return self.send_request('/moskva/kupit/kvartira/2,3-komnatnie/?priceMax={0}&page={1}'.format(price_max, page))

    @Handler_bad_case
    def set_new_proxy(self, new_proxy=None):
        while not new_proxy:
            new_proxy = self.proxy_switcher.get_new_proxy()
        self.session.proxies = {'https': new_proxy}

    @Handler_bad_case
    def send_request(self, url):
        self.session.headers.update({'Connection': 'close',
                                     'Accept': '*/*',
                                     'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                     'Cookie': '$Version=1',
                                     'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
                                     'User-Agent': self.user_agent})
        if url.find('http') == -1 and url.find('https') == -1:
            url = config.START_URL + url

        response = self.session.get(url)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            if 'showcaptcha' in response.url:
                raise Captcha
            self.LastPage = response.text
            return True
        else:
            if response.status_code == 429:
                sleep_minutes = 5
                time.sleep(sleep_minutes * 60)

    @Handler_bad_case
    def get_items_from_page(self, page_text):
        if not page_text:
            assert ValueError('Page not found!')
        items = BeautifulSoup(page_text, 'html.parser').find('div', {'class' : 'OffersSearchPage'})\
            .find('div', {'class': 'ContentWidth'}) \
            .find('div', {'class': 'ContentCol ContentCol_adaptive'}) \
            .find('div', {'class': 'ContentCol__main ContentCol__main_with_ads'})\
            .find('div', {'class': 'OffersSerp'})\
            .find('ol', {'class': 'OffersSerp__list'})
        return map(str, items)

    @Handler_bad_case
    def get_info_link(self, page_text):
        html = BeautifulSoup(page_text, 'html.parser')
        link_info = html.find_all('a', {'class': 'Link Link_js_inited Link_size_m Link_theme_islands '
                                                 'SerpItemLink OffersSerpItem__link OffersSerpItem__left'})
        if link_info is None:
            return ""

        name_link = ""
        for link in link_info:
            name_link = link
            break
        if type(name_link) != str:
            name_link = name_link.get('href')
        return get_full_url(name_link)

    @Handler_bad_case
    def get_info_address(self, page_text):
        html = BeautifulSoup(page_text, 'html.parser')
        address = html.find('div', {'class': 'OffersSerpItem__address'})
        if address is not None:
            return address.text.encode().decode('utf8')
        else:
            return ""

    @Handler_bad_case
    def get_info_description(self, page_text):
        html = BeautifulSoup(page_text, 'html.parser')

        if html.find('div', {'class': 'OffersSerpItem__generalInfo'}) is None:
            return ""
        if html.find('div', {'class': 'OffersSerpItem__generalInfo'}).find('a') is None:
            return ""
        if html.find('div', {'class': 'OffersSerpItem__generalInfo'}).find('a').find('h3') is None:
            return ""

        description = html.find('div', {'class': 'OffersSerpItem__generalInfo'}).find('a').find('h3')
        return description.text

    @Handler_bad_case
    def get_info_price(self, page_text, url):
        html = BeautifulSoup(page_text, 'html.parser')

        if html.find('div', {'class': 'OffersSerpItem__dealInfo'}) is None:
            return ""
        if html.find('div', {'class': 'OffersSerpItem__dealInfo'})\
                .find('div', {'class': 'Price OffersSerpItem__price'})is None:
            price = html.find('div', {'class': 'OffersSerpItem__dealInfo'}) \
                .find('div', {'class': 'Price Price_with-trend Price_interactive OffersSerpItem__price'})\
                .find('span', {'class': 'price'})
        else:
            price = html.find('div', {'class': 'OffersSerpItem__dealInfo'})\
                        .find('div', {'class': 'Price OffersSerpItem__price'}).find('span', {'class': 'price'})
        price = price.text
        if price == "":
            return
        new_price = ""
        for i in range(len(price)):
            if price[i].isdigit():
                new_price = new_price + price[i]
        price = price[ : len(price) - 1]
        if new_price == "":
            self.send_request(url)
            html = BeautifulSoup(self.LastPage, 'html.parser')

            if html.find('div', {'class': 'Price Price_with-trend Price_interactive'}) is None:
                return ""
            else:
                new_price = html.find('div', {'class': 'Price Price_with-trend Price_interactive'})\
                    .find('span', {'class': 'price'})
                new_price = new_price.text
                new_new_price = ""
                for i in range(len(new_price)):
                    if new_price[i].isdigit():
                        new_new_price = new_new_price + new_price[i]
                new_price = new_new_price
        return new_price

    @Handler_bad_case
    def get_info_image(self, url):
        self.send_request(url)
        html = BeautifulSoup(self.LastPage, 'html.parser')

        if html.find('div', {'class': 'GalleryThumbsSlider'}) is None:
            return ""

        list_of_images = html.find('div', {'class': 'GalleryThumbsSlider'})\
                             .findAll('div', {'class': 'GalleryThumbsThumb'})
        images = ""
        cnt = 0
        for image in list_of_images:
            a = image.find('img')['src']
            if a[a.rfind('/'):] != '/minicard':
                continue
            if cnt > 0:
                images = images + " " + 'https:' + a
            else:
                images = images + 'https:' + a
            cnt = 1
            images = images[:images.rfind('/')]
            images = images + '/large'
        images.lstrip()
        images.rstrip()
        return images

    @Handler_bad_case
    def get_info_item(self, page_text):
        link = self.get_info_link(page_text)
        if link == "":
            return {}

        address = self.get_info_address(page_text)
        if address == "":
            return {}

        description = self.get_info_description(page_text)
        if description == "":
            return {}

        images = self.get_info_image(link)
        if images == "":
            return {}
        images.lstrip()
        images.rstrip()
        description.lstrip()
        description.rstrip()
        price = self.get_info_price(page_text, link)
        return {
            'Link': link,
            'Description': description,
            'Photo': images,
            'Address': address,
            'Price': price
        }

    @Handler_bad_case
    def get_json(self, path='Yandex.json'):
        with io.open(path, 'w') as file:
            json.dump(Json, file, indent=4, ensure_ascii=False, separators=(',', ': '))
            file.close()


robot = Scraper()
for x in range(1, 24):
    robot.get_page(35000000, page=x)
    results = robot.get_items_from_page(robot.LastPage)
    if results:
        print(x)
        for item in results:
            info = robot.get_info_item(item)
            if info != {}:
                Json.append(info)
            print()
        robot.get_json()
    time.sleep(20 + 5 * random())
robot.get_json()

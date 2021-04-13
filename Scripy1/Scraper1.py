import json
import ssl
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
import config

class Scraper(object):
    def __init__(self):
        self.Json = []
        self.Not = ['4', '1', '5', '6', 'chetyreh', 'chetyrek', 'odno', 'pyati', 'shesti']

    def get_page_city(self):
        start = urlopen('https://kino-bank.com/listing-category/')
        html = BeautifulSoup(start)
        for category in html.find("div", {"class": "row-fruid row-subcat clearfix"}).findAll("div", {
            "class": "col-md-4 col-sm-4 col-xs-12"}):
            for nextCategory in category.find("div", {"class": "subcat-item"}).findAll('a', {"class": "subcat-link"}):
                nameCategory = config.START_URL + nextCategory.get('href')
                print(nameCategory)
                self.get_category(urlopen(nameCategory))
                break

    def get_category(self, start):
        html = BeautifulSoup(start)
        for category in html.find("div", {"class": "row-fruid row-subcat clearfix"}).findAll("div", {
            "class": "col-md-4 col-sm-4 col-xs-12"}):
            for nextCategory in category.find("div", {"class": "subcat-item"}).findAll('a', {"class": "subcat-link"}):
                nameCategory = config.START_URL + nextCategory.get('href')
                print(nameCategory)
                if 'apartments' in nameCategory or 'kvartiry' in nameCategory:
                    self.get_page(urlopen(nameCategory))
                    break

    def get_page(self, category):
        html = BeautifulSoup(category)
        for allRecords in html.find("div", {"class": "item-list row-fruid clearfix"}).findAll("div", {
            "class": "col-md-6 col-sm-6 col-xs-12"}):
            for record in allRecords.find("div", {"class": "cat-item"}).findAll('a', {"class": None}):
                nameRecord = config.START_URL + record.get('href')
                self.get_info(urlopen(nameRecord))
        addMore = html.find("div", {"class": "hidden cetegory_page_navi"})
        if addMore is not None:
            namePage = ""
            for nextPage in addMore.findAll('a'):
                namePage = namePage + ' ' + nextPage.get('href')
                print(namePage)
                self.get_page(urlopen(namePage))

    def get_link(self, html):
        Name_Link = ""
        for title in html.findAll("link", {"rel": "canonical"}):
            Name_Link = title.get('href')
        for id in self.Not:
            if id in Name_Link:
                return ""
        Name_Link.lstrip()
        Name_Link.rstrip()
        return Name_Link

    def get_description(self, html):
        description = ""
        name = html.find("div", {"class": "item-top"})
        if name is not None:
            title = name.find('h1')
            description = title.get_text()
        else:
            return
        o = html.find("div", {"class": "tab-content container"})
        extraInfo = o.find("div", {"class": "tab-pane active"})
        if extraInfo is not None:
            for info in extraInfo:
                info = str(info.string)
                info = re.sub('\s+', ' ', info)
                info = info[1:]
                description = description + info
        description.rstrip()
        description.lstrip()
        return description

    def get_photos(self, html):
        photo = ""
        for photoDiv in html.find("div", {"class": "gallery-container"}) \
                .find("div", {"class": "row row-item"}) \
                .find("div", {"class": "col-b-9 col-md-8 col-sm-7 col-xs-12"}) \
                .find("div", {"class": "row row-img"}) \
                .findAll("div", {"class": "col-md-3 col-sm-3 col-xs-6"}):
            for linkPhoto in photoDiv.findAll('a'):
                photo = photo + config.START_URL + linkPhoto.get('href') + ' '
        photo = photo[:len(photo) - 1]
        return photo

    def get_info(self, record):
        html = BeautifulSoup(record)
        Link = self.get_link(html)
        if Link == "":
            return
        Description = self.get_description(html)
        if Description == "":
            return

        Photo = self.get_photos(html)
        if Photo == "":
            return
        self.Json.append({"Link": Link, 'Description': Description, 'Photo': Photo, "Address": "", "Price": ""})


ssl._create_default_https_context = ssl._create_unverified_context
robot = Scraper()
robot.get_page_city()
with open('kino-bank1.json', 'w') as fout:
    json.dump(robot.Json, fout, indent=4, ensure_ascii=False, separators=(',', ': '))
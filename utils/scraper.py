from bs4 import BeautifulSoup
import json
import re
from typing import List, Union
import pandas as pd
from pandas.core.frame import DataFrame
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class Data:
    """
    This class stores all the data scraped from the websites and parses it.
    """
    def __init__(self, url: str):
        self.url: str = url

    def parse(self, data: dict) -> None:
        """
        Parses a dict and adds all data as class attributes

        :param data: Dictionarry containing data, containing info about house price, locations etc
        """
        for key, val in data.items():
            if val == '':
                val = None
            if (key == "id" or key == "visualisationOption" or key == "specificities" or key == "certificates"):
                pass
            elif (key == "atticExists"):
                self.attic = "Yes" if val == "true" else "No"
            elif (key == "basementExists"):
                self.basement = "Yes" if val == "true" else "No"
            elif (key == "bedroom"):
                self.bedrooms = data.get(key).get("count")
            elif (key == "building"):
                self.condition = data.get(key).get("condition")
                self.constructionYear = data.get(key).get("constructionYear")
            elif (key == "kitchen"):
                self.kitchen_type = data.get(key).get("type")
            elif (key == "land"):
                self.land_surface = data[key]["surface"]
            elif (key == "outdoor"):
                surf = data[key]["garden"]["surface"]

                self.garden_surface = surf if surf else 0
                self.terrace = "Yes" if data[key]["terrace"]["exists"] == "true" else "No"
            elif (key == "energy"):
                self.heating_type = data[key]["heatingType"]
            elif (key == "parking"):
                indoor = data[key]["parkingSpaceCount"]["indoor"]
                outdoor = data[key]["parkingSpaceCount"]["outdoor"]

                self.parking_indoor = indoor if indoor  != '' else 0
                self.parking_outdoor = outdoor if outdoor != '' else 0
            elif (key == "wellnessEquipment"):
                self.has_swimming_pool = "Yes" if val.get('hasSwimmingPool') == "true" else "No"
            else:
                # setattr creates a class attribute with the name "key" and the value "val"
                setattr(self, key, val)


class ImmoWebScraper:
    """
    """
    def __init__(self):
        self.driver_options = Options()
        self.driver_options.headless = True
        self.driver: webdriver.Firefox = webdriver.Firefox(executable_path='../../geckodriver/geckodriver.exe', options=self.driver_options)
        self.driver.implicitly_wait(2)

        self.data_list: List[Union[Data, None]] = []

    def __del__(self):
        self.driver.quit()

    def get_urls(self) -> None:
        """
        Cycle through all the search pages of immoweb, saving all the announcements found in a Data structure
        """
        # Cycle through every page in the search engine
        for i in range(1, 334):
            try:
                _URL = f"https://www.immoweb.be/en/search/house/for-sale?countries=BE&orderBy=relevance&page={i}"
                self.driver.get(_URL)
                # Search for every announcement links (30 par search page)
                for elem in self.driver.find_elements_by_xpath("//a[@class='card__title-link']"):
                    self.data_list.append(Data(elem.get_attribute("href")))
            except:
                print("Someting went wrong in url parsing")

    def scrap_data(self) -> None:
        """
        Executes js script in the web page (returning window.dataLayer object), then adds it to dataFrame
        Maybe will need some webscraping with bs4, if data is incomplete

        For performance, maybe rewrite with http requests, avoids rendering pages ten thousand times 
        """

        for i, data in enumerate(self.data_list):
            try:
                req = requests.get(data.url)
                if req.status_code == 429:
                    raise Exception("Too many requests")
                if req.status_code != 200:
                    raise Exception(f"Status code : {req.status_code}")
                soup = BeautifulSoup(req.content, "lxml")
                # Searches for the first script tag, in our case the dataLayer we need is the first script
                data_layer = soup.find("script")

                # Remove js components from script
                pattern = re.compile(r'^\s+window.dataLayer\s=\s\[\s+')
                pattern2 = re.compile(r'\s+\];$')
                if data_layer:  
                    raw = re.sub(pattern, '', data_layer.string)
                    raw = re.sub(pattern2, '', raw)
                    raw = json.loads(raw).get("classified")
                    # Removes house groupes & appartement groups
                    if raw.get("type") != "house group":
                        data.parse(raw)
                    else:
                        self.data_list[i] = None
                else:
                    raise Exception("DataLayer is undefined")
            except Exception as ex:
                self.data_list[i] = None
                print(ex)
            except:
                self.data_list[i] = None
                print("Someting bad happend")


    def fill_dataframe(self) -> None:
        """
        Converts all the objects present in self.data_list to dictionaries, then feed them to the dataframe.
        """
        self.data_list = [i for i in self.data_list if i != None]
        self.df: DataFrame = pd.DataFrame([data.__dict__ for data in self.data_list])
        self.df.replace({'': None, 'None': None})

import requests
from bs4 import BeautifulSoup
from typing import List, Set, Tuple
import functools
import operator

class PkpScraper:
    MAIN_PAGE = 'https://portalpasazera.pl/KatalogPolaczen?przewoznik='
    PAGE_NUMBER_MODIFIER = '&p='

    def __init__(self, carriers_names: List[str]):
        self.carriers_names = carriers_names
        self.nodes: Set[str] = set()
        self.edges: Set[Tuple[str, str]] = set()

    def scrape_one_carrier(self, carrier_name: str):
        main_url = PkpScraper.MAIN_PAGE + carrier_name
        main_page = requests.get(main_url)
        soup = BeautifulSoup(main_page.content, 'html.parser')
        last_page_number = self.get_num_pages_from_pagination(soup)
        for page_number in range(1, last_page_number+1):
            self.scrape_subpage(main_url, page_number)

    def get_num_pages_from_pagination(self, soup: BeautifulSoup):
        pagination = soup.find(attrs={'class': 'pagination'})
        num_pages_tag = list(pagination.children)[-4]
        a_tag = num_pages_tag.find(name='a')
        num_pages = int(a_tag.text)
        return num_pages

    def scrape_subpage(self, main_url: str, page_number: int):
        pass

    def scrape_one_route_page(self, route_url: str):
        page = requests.get(route_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        all_routes = soup.find_all(name='strong', attrs={'class': 'item-value'})
        stations_on_routes = [
            [station.text for station in route.find_all(name='span', attrs={'lang': 'pl-PL'})]
            for route in all_routes]
        self.create_nodes(stations_on_routes)
        self.create_edges(stations_on_routes)

    def create_nodes(self, stations_on_routes: List[List[str]]):
        stations_flat = functools.reduce(operator.iconcat, stations_on_routes, [])
        self.nodes.update(stations_flat)

    def create_edges(self, stations_on_routes: List[List[str]]):
        for route in stations_on_routes:
            self.create_edges_from_route(route)

    def create_edges_from_route(self, route: List[str]):
        new_edges = list(zip(route[:-1], route[1:]))
        self.edges.update(new_edges)


if __name__ == '__main__':
    URL = 'https://portalpasazera.pl/KatalogPolaczen?przewoznik=arriva-rp'
    URL = 'https://portalpasazera.pl/KatalogPolaczen?przewoznik=pkp-intercity-sp%C3%B3%C5%82ka-akcyjna&trasa=Gdynia+G%C5%82%C3%B3wna-Zielona+G%C3%B3ra%20G%C5%82%C3%B3wna'
    carriers = [
        'pkp-intercity-spółka-akcyjna'
    ]

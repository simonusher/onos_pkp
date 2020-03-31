import requests
from bs4 import BeautifulSoup
from typing import List, Set, Tuple, Dict
import functools
import operator
import re


class PkpScraper:
    MAIN_PAGE = 'https://portalpasazera.pl'
    MAIN_PAGE_CATALOG = MAIN_PAGE + '/KatalogPolaczen?przewoznik='
    PAGE_NUMBER_MODIFIER = '&p='

    def __init__(self, carriers_names: List[str]):
        self.carriers_names = carriers_names
        self.nodes: Set[str] = set()
        self.nodes_with_ids: Dict[str, int] = {}
        self.edges: Set[Tuple[str, str]] = set()
        self.verbose = False

    def scrape(self, verbose=False):
        self.verbose = verbose
        for carrier_name in self.carriers_names:
            self.scrape_one_carrier(carrier_name)

    def scrape_one_carrier(self, carrier_name: str):
        if self.verbose:
            print(f"Scraping: {carrier_name}")
        main_url = PkpScraper.MAIN_PAGE_CATALOG + carrier_name
        main_page = requests.get(main_url)
        soup = BeautifulSoup(main_page.content, 'html.parser')
        last_page_number = self.get_num_pages_from_pagination(soup)
        for page_number in range(1, last_page_number + 1):
            if self.verbose:
                print(f"\tPage: {page_number} of {last_page_number}")
            self.scrape_subpage(main_url, page_number)

    def get_num_pages_from_pagination(self, soup: BeautifulSoup):
        pagination = soup.find(attrs={'class': 'pagination'})
        num_pages_tag = list(pagination.children)[-4]
        a_tag = num_pages_tag.find(name='a')
        num_pages = int(a_tag.text)
        return num_pages

    def scrape_subpage(self, main_url: str, page_number: int):
        page_url = main_url + PkpScraper.PAGE_NUMBER_MODIFIER + str(page_number)
        page = requests.get(page_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        route_links = self.get_route_list(soup)
        for route_url in route_links:
            self.scrape_one_route_page(route_url)

    def get_route_list(self, soup: BeautifulSoup):
        links = soup.find_all(name='a', attrs={'class': 'loadScr'},
                              href=lambda href: href and re.compile("trasa").search(href))
        links = [PkpScraper.MAIN_PAGE + l['href'] for l in links]
        return links

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

    def save(self, filename: str):
        sorted_nodes = sorted(list(self.nodes))
        ids_nodes, nodes_ids = self.prepare_node_ids(sorted_nodes)
        with open(f"{filename}.nodes", "wt+") as f:
            f.write("id,name\n")
            for id, name in ids_nodes.items():
                f.write(f"{id},{name}\n")
        sorted_edges = sorted(list(self.edges))
        with open(f"{filename}.edges", 'wt+') as f:
            f.write("source,target\n")
            for source, destination in sorted_edges:
                f.write(f"{nodes_ids[source]}, {nodes_ids[destination]}\n")

    def prepare_node_ids(self, sorted_nodes: List[str]) -> Tuple[Dict[int, str], Dict[str, int]]:
        ids_into_nodes = {}
        reversed_nodes = {}
        for i, name in enumerate(sorted_nodes):
            ids_into_nodes[i] = name
            reversed_nodes[name] = i
        return ids_into_nodes, reversed_nodes


if __name__ == '__main__':
    carriers = [
        'pkp-intercity-spółka-akcyjna',
        # 'koleje-dolnośląskie',
        # 'koleje-mazowieckie-km',
        # 'koleje-małopolskie',
        # 'koleje-śląskie',
        # 'koleje-wielkopolskie',
        # 'polregio'
    ]
    scraper = PkpScraper(carriers)
    scraper.scrape(verbose=True)
    print(scraper.nodes)
    scraper.save("results")
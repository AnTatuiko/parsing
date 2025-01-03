'''
Proxy:

154.16.146.43

'''

from requests import Session
from bs4 import BeautifulSoup
import csv


class WebScraper:
    def __init__(self, start_url):
        self.start_url = start_url
        self.base_url = "/".join(start_url.split("/")[:-1]) + '/'
        self.session = Session()
        self.preview_details_keys = [
            'p_header',
            'article',
            'brand',
            'model',
            'in_stock',
            'price',
            'old_price'
        ]
        self.columns = ['Название', 'Артикул', 'Бренд', 'Модель', 'Наличие', 'Цена', 'Старая цена', 'Ссылка']
        self.data = []

    def fetch_soup(self, url):
        """Получает объект BeautifulSoup для указанного URL."""

        try:
            response = self.session.get(url)
            response.encoding = 'utf-8'
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            raise Exception(f"Ошибка при загрузке страницы {url}: {e}")

    def get_navigation_menu_urls(self):
        """Получаем ссылки на все разделы меню навигации."""

        soup = self.fetch_soup(self.start_url)
        pagination = soup.select_one("div.nav_menu")
        if not pagination:
            return []
        return [self.base_url + a.get("href") for a in pagination.select("a")]

    def get_pagination_urls(self, site):
        """Получает ссылки на все страницы пагинации."""
        
        soup = self.fetch_soup(site)
        pagination = soup.select_one("div.pagen")
        if not pagination:
            return []
        return [self.base_url + a.get("href") for a in pagination.select("a")]

    def get_item_card_urls(self, site):
        """Получение ссылок на все карточки товара на странице"""
        
        soup = self.fetch_soup(site)
        pagination = soup.select('a.name_item')
        if not pagination:
            return []
        return [f"{self.base_url}{link.get('href')}" for link in pagination]
    
    def get_page_items(self, url):
        """Возвращает элементы товаров на странице."""

        soup = self.fetch_soup(url)
        info = soup.select("div.item")
        if not info:
            info = soup.select("div.item_card")
        return info

    def get_preview_details(self, soup_element, site):
        """Извлекает данные товара из HTML-элемента."""

        preview_details = {}
        for key in self.preview_details_keys:
            
            if isinstance(key, str):
                element = soup_element.select_one(f".{key}")
                if not element:
                     element = soup_element.select_one(f"#{key}")
                if key in ('p_header', 'price', 'old_price'):
                    preview_details[key] = element.get_text(strip=True) if element else None
                else:
                    preview_details[key] = element.get_text(strip=True).split(': ')[1].strip() if element else None 
        preview_details['link'] = site
        return preview_details

    def scrape(self):
        """Основной метод для запуска сбора данных."""

        navigation_urls = self.get_navigation_menu_urls()      
        all_data = []
        for nav_url in navigation_urls:
            self.base_url = "/".join(nav_url.split("/")[:-1]) + '/'
            pagination_urls = self.get_pagination_urls(nav_url)
            for page_url in pagination_urls:
                cards_url = self.get_item_card_urls(page_url)
                for card_url in cards_url:
                    page_items = self.get_page_items(card_url)
                    for item in page_items:
                        all_data.append(self.get_preview_details(item, card_url))
            self.data = all_data
        return all_data

    def csv_save(self, fname=None):
        """Сохраняет данные в CSV-файл."""

        fname = fname or f"{self.base_url.split('/')[2]}.csv"
        if not self.data:
            self.scrape()
        try:
            with open('pars.csv', mode='w', encoding='utf-8-sig', newline='') as file:               
                writer = csv.writer(file, delimiter=';')
                writer.writerow(self.columns)
                for row in self.data:
                    writer.writerow(row.values())
        except Exception as e:
            raise Exception(f"Ошибка при записи файла {fname}: {e}")

if __name__ == "__main__":
    start_url = "https://parsinger.ru/html/index1_page_1.html"
    scraper = WebScraper(start_url)
    scraper.scrape()
    scraper.csv_save()
    scraper.session.close()
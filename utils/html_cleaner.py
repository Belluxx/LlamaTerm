import requests
from bs4 import BeautifulSoup, Comment
import re

class HTMLCleaner:
    @classmethod
    def fetch_and_clean_html(cls, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            original_html = response.text
            original_length = len(original_html)

            soup = BeautifulSoup(original_html, 'html.parser')

            cls._remove_unwanted_elements(soup)
            cls._remove_comments(soup)
            cls._replace_links_with_text(soup)
            cls._remove_attributes(soup)
            cls._clean_text_nodes(soup)

            cleaned_html = str(soup)
            cleaned_length = len(cleaned_html)

            reduction_percentage = cls._calculate_reduction(original_length, cleaned_length)

            return cleaned_html, reduction_percentage

        except requests.RequestException as e:
            raise Exception(f"Error fetching the URL: {e}")

    @staticmethod
    def _remove_unwanted_elements(soup):
        for element in soup(["script", "style", "iframe", "img"]):
            element.decompose()

    @staticmethod
    def _remove_comments(soup):
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

    @staticmethod
    def _replace_links_with_text(soup):
        for a in soup.find_all('a'):
            a.replace_with(a.get_text())

    @staticmethod
    def _remove_attributes(soup):
        for tag in soup.find_all(True):
            tag.attrs = {}

    @classmethod
    def _clean_text_nodes(cls, soup):
        for element in soup.find_all(text=True):
            if element.parent.name not in ['script', 'style']:
                cleaned_text = cls._clean_text(element.string) + '\n'
                element.replace_with(cleaned_text)

    @staticmethod
    def _clean_text(text):
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def _calculate_reduction(original_length, cleaned_length) -> float:
        if original_length == 0:
            return 0
        return ((original_length - cleaned_length) / original_length) * 100.0

import requests
from bs4 import BeautifulSoup, Comment

class HTMLCleaner:
    @classmethod
    def fetch_and_clean_html(cls, url: str) -> tuple[str, float]:
        """
        Fetches HTML content from a given URL, cleans it, and returns the cleaned HTML along with the reduction percentage.

        @param url: The URL of the webpage to fetch and clean
        @return: A tuple containing the cleaned HTML and the reduction percentage
        @raises Exception: If there's an error fetching the URL
        """
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
    def _remove_unwanted_elements(soup: BeautifulSoup) -> None:
        """
        Removes unwanted elements from the BeautifulSoup object.

        @param soup: The BeautifulSoup object to clean
        """
        for element in soup(["script", "style", "iframe", "img"]):
            element.decompose()

    @staticmethod
    def _remove_comments(soup: BeautifulSoup) -> None:
        """
        Removes comments from the BeautifulSoup object.

        @param soup: The BeautifulSoup object to clean
        """
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

    @staticmethod
    def _replace_links_with_text(soup: BeautifulSoup) -> None:
        """
        Replaces link tags with their text content in the BeautifulSoup object.

        @param soup: The BeautifulSoup object to clean
        """
        for a in soup.find_all('a'):
            a.replace_with(a.get_text())

    @staticmethod
    def _remove_attributes(soup: BeautifulSoup) -> None:
        """
        Removes all attributes from tags in the BeautifulSoup object.

        @param soup: The BeautifulSoup object to clean
        """
        for tag in soup.find_all(True):
            tag.attrs = {}

    @classmethod
    def _clean_text_nodes(cls, soup: BeautifulSoup) -> None:
        """
        Cleans text nodes in the BeautifulSoup object.

        @param soup: The BeautifulSoup object to clean
        """
        for element in soup.find_all(text=True):
            if element.parent.name not in ['script', 'style']:
                cleaned_text = cls._clean_text(str(element)) + '\n'
                element.replace_with(cleaned_text)

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Cleans a given text by removing extra whitespace.

        @param text: The text to clean
        @return: The cleaned text
        """
        return ' '.join(text.split())

    @staticmethod
    def _calculate_reduction(original_length: int, cleaned_length: int) -> float:
        """
        Calculates the reduction percentage between the original and cleaned HTML lengths.

        @param original_length: The length of the original HTML
        @param cleaned_length: The length of the cleaned HTML
        @return: The reduction percentage
        """
        if original_length == 0:
            return 0.0
        return ((original_length - cleaned_length) / original_length) * 100.0

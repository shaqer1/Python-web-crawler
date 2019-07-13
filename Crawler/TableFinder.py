from html.parser import HTMLParser
import urllib.parse
import functions
from UrlFinder import UrlFinder


class TableFinder(UrlFinder):
    def __init__(self, page_url):
        UrlFinder.__init__(self, page_url, 'table', 'class')

from html.parser import HTMLParser
import urllib.parse
import functions
from UrlFinder import UrlFinder


class TagFinder(UrlFinder):
    def __init__(self, page_url, tag, attr):
        UrlFinder.__init__(self, page_url, tag, attr)

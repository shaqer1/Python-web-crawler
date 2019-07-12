import urllib.parse
from Crawler.LinkFinder import LinkFinder
import Models.Queue.Image
import Models.Queue.Link


class Link:
    def __init__(self, page_url):

        self.LinkExt = Models.Queue.Link.Link()
        self.link = Models.Queue.Link.Link()

        self.page_url = page_url
        urlres = urllib.parse.urlparse(page_url)
        self.base_url = urlres.netloc
        self.linksSet = set()

    def add(self, link):
        full_url = self.sanitize_url(link)
        if full_url:
            self.linksSet.add(full_url)
        return self

    def fetch_links(self):
        """
        Get all the anchor tag url from the website
        :return:
        """
        link_finder = LinkFinder(self.page_url)
        link_finder.feed(link_finder.html_string())
        self.linksSet = link_finder.get_values()
        return self.linksSet

    def links(self):
        return self.linksSet

    def _merge_links(self):
        for lk in self.linksSet:
            self.LinkExt.add(lk)
        return self.LinkExt.links

    def save(self):
        self._merge_links()
        self.LinkExt.save()

    def save_links(self):
        self.fetch_links()
        self.save()
        self.update_link()

    def update_link(self):
        self.link.remove(self.page_url)
        self.link.save()

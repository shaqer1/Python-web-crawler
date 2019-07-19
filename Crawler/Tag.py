import urllib.parse
from Crawler.TagFinder import TagFinder
from bs4 import BeautifulSoup
import Models.Queue.Tag
import Models.Queue.Link


class Tag:
    def __init__(self, base_url, page_url, tag, attr, tagMap = {}, tagMapQ = None):

        self.tag = Models.Queue.Tag.Tag()
        self.link = Models.Queue.Link.Link()
        self.html_string = ""
        self.tag = tag
        self.attr = attr
        self.tagMap = tagMap
        self.tagMapQ = tagMapQ
        self.page_url = page_url
        urlres = urllib.parse.urlparse(page_url)
        self.base_url = base_url
        self.scheme = urlres.scheme
        self.tags = set()

    def add(self, link):
        full_url = self.sanitize_url(link)
        if full_url:
            self.tags.add(full_url)
        return self

    def fetch_links(self, html):
        """
        Get all the anchor tag url from the website
        :return:
        """
        try:
            tag_finder = TagFinder(self.page_url, self.tag, self.attr)
            if(html == ""):
                self.html_string = tag_finder.html_string()
            else:
                self.html_string = html

            if self.tagMap != None and self.html_string != None:
                soup = BeautifulSoup(self.html_string, features="lxml")
                div = soup(self.tag, {self.attr : self.tagMapQ})
                if len(div)>0:
                    children = div[0].findChildren()
                    # print(children)
                    for (tag, attr) in self.tagMap.items():
                        for i in children:
                            if i.name == tag and attr in i.attrs:
                                self.tags.add(urllib.parse.urljoin(self.scheme + "://" + self.base_url, i.attrs[attr]))
            else:
                self.tags = tag_finder.get_values()
                tag_finder.feed('<html></html>' if  self.html_string == None else self.html_string)

            return self.tags
        except Exception as e:
            print(e, 'in tag.py', self.page_url)
            return self.tags

    def addTagMap(self, tagMap):
        self.tagMap = tagMap

    def addTagMapQuery(self, tagMapQ):
        self.tagMapQ = tagMapQ

    def links(self):
        return self.tags

    def _merge_links(self):
        for lk in self.tags:
            self.tag.add(lk)
        return self.tag.tags

    def save(self):
        self._merge_links()
        self.tag.save()

    def save_links(self):
        self.fetch_links("")
        self.save()
        self.update_link()

    def update_link(self):
        self.link.remove(self.page_url)
        self.link.save()
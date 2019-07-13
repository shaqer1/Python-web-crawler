import urllib.parse
from Crawler.TableFinder import TableFinder
import Models.Queue.Image
import Models.Queue.Link
import Models.Queue.Table


class Table:
    def __init__(self, page_url):

        self.TableExt = Models.Queue.Table.Table()
        self.table = Models.Queue.Table.Table()
        self.html_string = ""

        self.page_url = page_url
        urlres = urllib.parse.urlparse(page_url)
        self.base_url = urlres.netloc
        self.tableSet = set()

    def add(self, table):
        full_url = self.sanitize_url(table)
        if full_url:
            self.tableSet.add(full_url)
        return self

    def fetch_links(self, html):
        """
        Get all the anchor tag url from the website
        :return:
        """
        table_finder = TableFinder(self.page_url)
        if(html == ""):
            self.html_string = table_finder.html_string()
        else:
            self.html_string = html
        table_finder.feed( '<html></html>' if  self.html_string == None else self.html_string )
        self.tableSet = table_finder.get_values()
        return self.tableSet

    def links(self):
        return self.tableSet

    def _merge_links(self):
        for lk in self.tableSet:
            self.TableExt.add(lk)
        return self.TableExt.links

    def save(self):
        self._merge_links()
        self.TableExt.save()

    def save_links(self):
        self.fetch_links()
        self.save()
        self.update_link()

    def update_link(self):
        self.table.remove(self.page_url)
        self.table.save()

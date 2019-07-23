import urllib.parse
from Crawler.FormFinder import FormFinder
import Models.Queue.Form
import Models.Queue.Link


class Form:
    def __init__(self, page_url):

        self.form = Models.Queue.Form.Form()
        self.link = Models.Queue.Link.Link()
        self.html_string = ""

        self.page_url = page_url
        urlres = urllib.parse.urlparse(page_url)
        self.scheme = urlres.scheme
        self.base_url = urlres.netloc
        self.forms = set()

    def add(self, link):
        full_url = self.sanitize_url(link)
        if full_url:
            self.forms.add(full_url)
        return self

    def fetch_links(self, html):
        """
        Get all the anchor tag url from the website
        :return:
        """
        form_finder = FormFinder(self.page_url)
        if(html == ""):
            self.html_string = form_finder.html_string()
        else:
            self.html_string = html
        form_finder.feed('<html></html>' if  self.html_string == None else self.html_string)
        self.forms = form_finder.get_values()
        return self.forms

    def links(self):
        return self.forms

    def _merge_links(self):
        for lk in self.forms:
            self.form.add(lk)
        return self.form.forms

    def save(self):
        self._merge_links()
        self.form.save()

    def save_links(self):
        self.fetch_links()
        self.save()
        self.update_link()

    def update_link(self):
        self.link.remove(self.page_url)
        self.link.save()

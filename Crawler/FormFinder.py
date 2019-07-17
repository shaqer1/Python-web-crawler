from UrlFinder import UrlFinder


class FormFinder(UrlFinder):
    def __init__(self, page_url):
        UrlFinder.__init__(self, page_url, 'form', 'id')

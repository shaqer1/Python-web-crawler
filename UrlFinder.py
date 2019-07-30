from html.parser import HTMLParser
import urllib.parse
import functions
from bs4 import BeautifulSoup
from Crawler.PageUrl import PageUrl
from requests import session
from lxml import html



class UrlFinder(HTMLParser):
    def __init__(self, page_url, tag, attr):
        self.page_url = page_url
        urlres = urllib.parse.urlparse(page_url)
        self.base_url = urlres.netloc
        self.scheme = urlres.scheme
        self.values = set()
        self.tag = tag
        self.attr = attr
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        """
        This function called by HTMLParser internally. We modify it to make our work

        :rtype: object
        """
        if tag == self.tag:
            for (attr, value) in attrs:
                if attr == self.attr:
                    fullUrl = urllib.parse.urljoin(self.scheme + "://" + self.base_url, value)
                    self.values.add(fullUrl)
                else:
                    continue

    def get_values(self) -> object:
        """
        List of image link as set
        :return: object
        """
        return self.values

    def __setattr__(self, name, value):
        """
        page url must be a valid domain.
        :param name:
        :param value:
        :return:
        """
        if name == 'page_url':
            result = urllib.parse.urlparse(value);

            if len(result.scheme) > 0 and len(result.netloc) > 0:
                self.__dict__[name] = value
            else:
                raise Exception('Invalid url')

        else:
            self.__dict__[name] = value

    def error(self, message):
        pass

    def html_string(self, authSession=None) -> object:
        """
        Fetch html from url and return as Html String
        :param page_url:
        :rtype: object
        """
        html_string = ''
        try:
            authenticity_token = None
            if authSession and not authSession.alwaysAuth:
                # -------------------------------Original------------------------------
                request = urllib.request.Request(self.page_url, headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
                response = urllib.request.urlopen(request)
                if 'text/html' in response.getheader('Content-Type'):
                    html_bytes = response.read()
                    html_string = html_bytes.decode("utf-8")
                    tree = html.fromstring(html_string)
                    try:
                        authenticity_token = list(set(tree.xpath("//input[@name='{authKey}']/@value".format(authKey=authSession.authKey))))[0]
                    except Exception as e:
                        authenticity_token = None

                # check if soup has form action then check payload post response and proceed with 200

            
            if (authenticity_token or authSession.alwaysAuth) and authSession:
                #print('Authenticating: ',self.page_url)
                html_string = authSession.getPage(self.page_url)

        except Exception as e:
            print('\n', e, 'link', self.page_url, '\n')
            return None
        return html_string
    
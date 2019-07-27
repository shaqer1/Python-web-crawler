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
        # try:
        #     resp = wget.download(self.page_url)
        #     # resp = requests.get(self.page_url, allow_redirects=True)
        #     html_string = resp
        # except Exception as e:
        #     return None
        # return html_string

        try:
            # driver = webdriver.PhantomJS()
            # driver.get(self.page_url)
            # soup = driver
            #request = urllib.request.Request(self.page_url)
            # , headers={
            #     "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
            #     }
            # session = HTMLSession()
            # # r = session.get(self.page_url)
            # session.browser
            # def render_html():
            #     r = session.get(self.page_url)
            #     r.html.render()

            # t = threading.Thread(target=render_html)
            # t.start()
            # r.html.render()
            # html_string = r.html.html
            # response = bs(urllib.request.urlopen(self.page_url), 'html.parser')
            # if 'text/html' in response.getheader('Content-Type'):
            #     html_bytes = response.read()
            #     html_string = html_bytes.decode("utf-8")

            # request = urllib.request.Request(self.page_url, headers={
            #     "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
            # response = urllib.request.urlopen(request)
            # soup = BeautifulSoup(response,'lxml')
            # tfp = tempfile.NamedTemporaryFile(delete=True)
            # tfp = wget.download(self.page_url)
            # tfp = open(tfp)
            # urllib.request.urlretrieve
            # html_string = ''

            # driver = webdriver.PhantomJS()
            # driver.get(self.page_url)
            # p_element = driver.find('form')
            # print(p_element.text)
            # if 'text/html' in response.getheader('Content-Type'):
            #     html_bytes = response.read()
            #     html_string = html_bytes.decode("utf-8")

            # html_string = soup.find('form')


            # -------------------------------Original------------------------------
            request = urllib.request.Request(self.page_url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
            response = urllib.request.urlopen(request)
            if 'text/html' in response.getheader('Content-Type'):
                html_bytes = response.read()
                html_string = html_bytes.decode("utf-8")
                tree = html.fromstring(html_string)
                try:
                    authenticity_token = list(set(tree.xpath("//input[@name='__RequestVerificationToken']/@value")))[0]
                except Exception as e:
                    authenticity_token = None

            # check if soup has form action then check payload post response and proceed with 200

            
            if authenticity_token and authSession:
                # print('Authenticating: ',self.page_url)
                html_string = authSession.getPage(self.page_url)
            # with session() as c:
            #     result = c.get('https://edwardsuatnewbrand.azurewebsites.net/gb/')
            #     # c.post('https://edwardsuatnewbrand.azurewebsites.net/gb/Users/Account/AccessDenied?ReturnUrl=/gb/', data=payload)
            #     tree = html.fromstring(result.text)
            #     authenticity_token = list(set(tree.xpath("//input[@name='__RequestVerificationToken']/@value")))[0]
                

            #     payload = {
            #         '__RequestVerificationToken': authenticity_token,
            #         'userNameOrEmail': 'uafzal@xavor.com',
            #         'password': 'Xavor123',
            #         'rememberMe': True
            #     }


            #     header = {
            #         'Connection': 'keep-alive',
            #         'Cache-Control': 'max-age=0',
            #         'Origin': 'http://edwardsuatnewbrand.azurewebsites.net',
            #         'Upgrade-Insecure-Requests': '1',
            #         'Content-Type': 'application/x-www-form-urlencoded',
            #         'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
            #         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            #         'Referer': 'http://edwardsuatnewbrand.azurewebsites.net/gb/Users/Account/AccessDenied?ReturnUrl=/gb/',
            #         'Accept-Encoding': 'gzip, deflate',
            #         'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            #         'Cookie': 'ARRAffinity=cda73737958c13848f3c08e4f40b30e22baa9f5cf321a34898f98f73ec3b8272; _ga=GA1.3.63132184.1564212695; _gid=GA1.3.777391251.1564212695; _gat_UA-75750319-1=1'
            #     }

            #     result = c.post(
            #                     'http://edwardsuatnewbrand.azurewebsites.net/gb/Users/Account/LogOn?ReturnUrl=/gb/', 
            #                     data = payload,
            #                     headers = header
            #                 )

            #     response = c.get('https://edwardsuatnewbrand.azurewebsites.net/gb/')

            #     # print('response.headers',response.headers)
            #     print('response.text',response.text)

        except Exception as e:
            print('\n', e, 'link', self.page_url, '\n')
            return None
        return html_string
    
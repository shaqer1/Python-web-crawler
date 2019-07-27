from bs4 import BeautifulSoup
import requests
from lxml import html


class AuthSession():
    def __init__(self, authJSON, authKey):
        self.authJSON = authJSON
        self.parseConfig(authJSON)
        self.authKey = authKey
        self.session = requests.Session()
        self.result = None
        self.authenticity_token = ''

    def parseConfig(self, config):
        self.headers = config['headers']
        self.loginURL = config['loginURL']
        self.authURL = config['authURL']
        self.payload = config['payload']

    def createSession(self):
        self.result = self.session.get(self.authURL)
        tree = html.fromstring(self.result.text)
        self.authenticity_token = list(set(tree.xpath("//input[@name='{tokenKey}']/@value".format(tokenKey=self.authKey))))[0]
        self.loginSession(self.authenticity_token)

    def loginSession(self, token):
        self.payload[self.authKey]=token
        self.result = self.session.post(
            self.loginURL,
            data = self.payload,
            headers = self.headers
        )

    def getPage(self, url):
        return self.session.get(url).text
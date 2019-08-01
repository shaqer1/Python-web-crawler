import os.path
import sys
import threading
import time
from queue import Queue
from Models.Complete.Image import Image
from Models.Complete.Form import Form
from Models.Complete.Link import Link
from Models.Complete.Table import Table
import math

import functions
from Crawler.Form import Form
from Crawler.Tag import Tag
from Crawler.Image import Image
from Crawler.Link import Link
from Crawler.Page import Page
from Crawler.Table import Table
from Image import Save
from Image.Download import Download
from Auth.AuthSession import AuthSession
import json


usage = 'usage: TODO'

PARAMTAGS = [
    'u',
    't',
    'e',
    'ext',
    'threads',
    'f',
    'tag',
    'child',
    'csv',
    'authA',
    'auth',
    'i',
    'l',
    'filterBase',
    'layers'
]

if __name__ == '__main__':
    params = {}

    # if len(sys.argv)%2!=1: #TODO add extension for start and baseurl,
    #     print('wrong number of args', usage)
    #     quit()

    for i in range(len(sys.argv)):
        if('-'==sys.argv[i][0]):
            if sys.argv[i][1:len(sys.argv)] in PARAMTAGS:
                if sys.argv[i][1:len(sys.argv)] == 'tag':
                    params[sys.argv[i][1:len(sys.argv)]] = [sys.argv[i+1],sys.argv[i+2],sys.argv[i+3]]
                elif sys.argv[i][1:len(sys.argv)] == 'auth' or sys.argv[i][1:len(sys.argv)] == 'authA':
                    params[sys.argv[i][1:len(sys.argv)]] = [sys.argv[i+1],sys.argv[i+2]]
                else:
                    params[sys.argv[i][1:len(sys.argv)]]=sys.argv[i+1]
            else:
                print(usage)
                quit()
            

    # print(params)
    URL = params['u']
    NUMBER_OF_THREADS = 4
    if 'threads' in params:
        NUMBER_OF_THREADS = int(params['threads'])
    if 'csv' in params:
        open(params['csv'], "w").close()
    if 'auth' in params or 'authA' in params:
        key = 'auth' if 'auth' in params else 'authA'
        with open(params[key][0]) as config_file:
            authConfig = json.load(config_file)
            authSession = AuthSession(authConfig, params[key][1], key)
            authSession.createSession()
            print('auth created')

    queue = Queue()
    domaincrwlQ = Queue()
    domaincrwlCurrQ = set()
    threads = []
    lock = threading.Lock()
    lock1 = threading.Lock()

    page = Page(URL + ('' if 'ext' not in params else params['ext']))
    links = set()
    visited = {}

    def createDomainWorkers():
        for _ in range(NUMBER_OF_THREADS):
            t=threading.Thread(target=fetch_links)
            t.daemon = True
            t.start()
            threads.append(t)

    def fetch_links():
        while True:
            try:
                with lock1:
                    link = domaincrwlQ.get()
                    domaincrwlCurrQ.add(link)
                page = Page(link)

                if page.page_url not in visited:
                    linksFound = filterURL(page.fetch_links("", '' if 'auth' not in params and 'authA' not in params else authSession), URL)
                    visited[page.page_url] = page.html_string
                    # l1 = domaincrwlQ.qsize() +len(visited)+1
                    
                    for item in linksFound:#TODO concurrency error
                        item = item.strip()
                        if item[-1]=='/':
                                item=item[0:-1]
                        if item not in domaincrwlQ.queue and item not in visited and item not in domaincrwlCurrQ:
                            domaincrwlQ.put(item)
                    
                    with lock:
                        print(threading.current_thread().name + ' fetched URL:' + link, 'found', domaincrwlQ.qsize() +len(visited)+1, 'visited', len(visited))
                    checkUnique(visited)
                    # if l1!=(domaincrwlQ.qsize() +len(visited)+1):
                    #     print('found', domaincrwlQ.qsize() +len(visited)+1, 'visited', len(visited))     
                domaincrwlCurrQ.remove(link)
                domaincrwlQ.task_done()
                if domaincrwlQ.empty():
                    break
            except Exception as e:
                print(e.args, link)
                domaincrwlQ.task_done()
                continue

    def checkUnique(visited):
        if len(visited) > len(set(visited.keys())):
            print('----------------------------------------NON UNIQUE ELEMENT----------------')

    def create_jobs():
        for link in sorted(links):
            #if ('https://' + URL) in link or ('http://' + URL) in link:
            queue.put(link)
            # print(link)
        queue.join()


    # Create worker threads (will die when main exits)
    def create_workers():
        for _ in range(NUMBER_OF_THREADS):
            t = threading.Thread(target=downloading)
            t.daemon = True
            t.start()

    def printJSON(imagesJSON):
        for x in imagesJSON:
            print("%s" % x)

    def downloading():
        while True:
            try:
                link = queue.get()
                
                html = ""
                if(link in visited):
                    html = visited[link]

                linksOBJ = []
                images = []
                tables = []
                tags = []
                forms = []
                
                if 'i' in params:
                    img = Image(link) 
                    if(link in visited):
                        html = visited[link]
                    images = img.fetch_links(html, '' if 'auth' not in params and 'authA' not in params else authSession)
                    visited[link] = img.html_string
                    images = filterNonImages(images, params['i'])

                
                if 'l' in params:
                    linkOBJ = Link(link)
                    if(link in visited):
                        html = visited[link]
                    linksOBJ = linkOBJ.fetch_links(html, '' if 'auth' not in params and 'authA' not in params else authSession)
                    visited[link] = linkOBJ.html_string
                    linksOBJ = filterNonLinks(linksOBJ, params['l'])

                if 't' in params:
                    table = Table(link)
                    if(link in visited):
                        html = visited[link]
                    tables = table.fetch_links(html, '' if 'auth' not in params and 'authA' not in params else authSession)
                    visited[link] = table.html_string

                if 'f' in params:
                    form = Form(link) 
                    if(link in visited):
                        html = visited[link]
                    forms = filterForms(form.fetch_links(html, '' if 'auth' not in params and 'authA' not in params else authSession), params['f'])
                    visited[link] = form.html_string

                if 'tag' in params:
                    tag = Tag(link, params['tag'][0], params['tag'][1])
                    if(link in visited):
                        html = visited[link]
                    if 'child' in params:
                        tagMap = parseArgs(params['child'])
                        tag.addTagMap(tagMap)
                        tag.addTagMapQuery(params['tag'][2])
                    tags = tag.fetch_links(html, '' if 'auth' not in params and 'authA' not in params else authSession)
                    visited[link] = tag.html_string

                with lock:
                    if 'csv' in params:
                        if(len(linksOBJ)>0 or len(images)>0 or len(tables) > 0 or len(forms)>0 or len(tags)>0):
                            print(threading.current_thread().name + ' fetched URL:' + link)
                        if(len(tags)> 0):
                            if 'filterBase' in params:
                                filterB = params['filterBase']
                            else:
                                filterB = ''
                            with open(params['csv'], "a") as myfile:
                                myfile.write(generateCSV(link, tags, filterB))
                        if(len(forms)> 0):
                            with open(params['csv'], "a") as myfile:
                                myfile.write(generateCSV(link, forms, form.scheme + "://" + form.base_url))
                        if len(linksOBJ)>0:
                            if 'filterBase' in params:
                                filterB = params['filterBase']
                            else:
                                filterB = ''
                            with open(params['csv'], "a") as myfile:
                                myfile.write(generateCSV(link, linksOBJ,filterB))
                    else:
                        if(len(linksOBJ)>0 or len(images)>0 or len(tables) > 0 or len(forms)>0 or len(tags)>0):
                            print(threading.current_thread().name + ' fetched URL:' + link)

                        if(len(linksOBJ)>0):
                            print('------Links-----')
                            printJSON(linksOBJ)

                        if(len(images)>0):
                            print('\n\n------Images-----')
                            printJSON(images)
                        
                        if(len(tables)> 0):
                            print('\n\n------Tables class-----')
                            printJSON(tables)
                        
                        if(len(forms)> 0):
                            print('\n\n------Forms id-----')
                            printJSON(forms)
                        
                        if(len(tags)> 0):
                            print('\n\n------Tags in child id-----')
                            printJSON(tags)

                        if(len(linksOBJ)>0 or len(images)>0 or len(tables) > 0 or len(forms)>0 or len(tags)>0):
                            print('END\n\n')

                # down = Download(links=images, path=functions.get_folder_name(link))
                # down.start()

                queue.task_done()
                if queue.empty():
                    break
            except Exception as e:
                print(e, link)
                queue.task_done()
                continue

    def generateCSV(link, tags, filterB):
        s = link +','
        for i in tags:
            if filterB != '' and filterB in i:
                i=i.replace(filterB, '')
            s+=i+','
        s=s[0:-1]
        s+='\n'
        return s

    def parseArgs(argsStr):
        tagMap = {}
        # argsStr = argsStr.replace('{','')
        #  argsStr = argsStr.replace('}','')
        args = argsStr.split('-')
        for i in args:
            pairs = i.split(':')
            tagMap[pairs[0].replace('\"','')] = pairs[1].replace('\"','')
        
        return tagMap
            

    def scrapeLinks(page, URL, links, visited, count, final):
        if page.page_url not in visited and count < final:
            l1 = len(links)
            linksFound = filterURL(page.fetch_links("", '' if 'auth' not in params and 'authA' not in params else authSession), URL)
            links = links.union(linksFound)
            visited[page.page_url] = page.html_string
            if l1 == len(links):
                return links
            print('found', len(links), 'visited', len(visited))
            for link in links:
                links = scrapeLinks(Page(link), URL, links, visited, count+1, final)
            return links
        return links
    
    def filterURL(links, URL):
        # links = filter(lambda link: , links)
        return [ x for x in set(links) if (URL) in x ]
        
    def filterNonImages(images, delim):
        return [ x for x in set(images) if delim not in x and 
                    x != 'https://dev.edwards.com/wp-content/mu-plugins/app/vendor/edwards/toolkit-php-components/dist/images//logo-white-text.png'  and 
                    x != 'https://dev.edwards.com/wp-content/plugins/ed-button/assets/images/ajax-loader.gif']
    
    def filterNonLinks(links, delim):
        return [ x for x in set(links) if delim not in x ]
    
    def filterForms(links, delim):
        return [ x for x in set(links) if delim in x ]

    
    # session = HTMLSession()
    # r = session.get(page.page_url)
    # #session.browser
    # r.html.render()
        
    if 'e' not in params:#TODO comment out
        start_time = time.time()
        if 'threads' not in params:
            links = scrapeLinks(page, URL, links, visited, 0, math.inf if 'layers' not in params else int(params['layers']))
            # printJSON(links)
            print('Found ',len(links), ' Links')
        else:
            createDomainWorkers()
            domaincrwlQ.put(URL + ('' if 'ext' not in params else params['ext']))
            domaincrwlQ.join()
            print('Found ',len(visited.keys()), ' Links')
            links = list(visited.keys())
        print("---URL scraping time %s seconds ---" % (time.time() - start_time))


    start_time = time.time()

    # links .json
    if 'e' in params:
        with open(params['e']) as config_file:
            links = json.load(config_file)['links']

    create_workers()
    create_jobs()
    print("---URL scraping time %s seconds for gb urls with /sites/ ---" % (time.time() - start_time))

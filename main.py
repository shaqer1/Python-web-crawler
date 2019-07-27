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
                elif sys.argv[i][1:len(sys.argv)] == 'auth':
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
    if 'auth' in params:
        with open(params['auth'][0]) as config_file:
            authConfig = json.load(config_file)
            authSession = AuthSession(authConfig, params['auth'][1])
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
                    linksFound = filterURL(page.fetch_links("", '' if 'auth' not in params else authSession), URL)
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
                    images = img.fetch_links(html, '' if 'auth' not in params else authSession)
                    visited[link] = img.html_string
                    images = filterNonImages(images, params['i'])

                
                if 'l' in params:
                    linkOBJ = Link(link)
                    if(link in visited):
                        html = visited[link]
                    linksOBJ = linkOBJ.fetch_links(html, '' if 'auth' not in params else authSession)
                    visited[link] = linkOBJ.html_string
                    linksOBJ = filterNonLinks(linksOBJ, params['l'])

                if 't' in params:
                    table = Table(link)
                    if(link in visited):
                        html = visited[link]
                    tables = table.fetch_links(html, '' if 'auth' not in params else authSession)
                    visited[link] = table.html_string

                if 'f' in params:
                    form = Form(link) 
                    if(link in visited):
                        html = visited[link]
                    forms = filterForms(form.fetch_links(html, '' if 'auth' not in params else authSession), params['f'])
                    visited[link] = form.html_string

                if 'tag' in params:
                    tag = Tag(URL, link, params['tag'][0], params['tag'][1])
                    if(link in visited):
                        html = visited[link]
                    if 'child' in params:
                        tagMap = parseArgs(params['child'])
                        tag.addTagMap(tagMap)
                        tag.addTagMapQuery(params['tag'][2])
                    tags = tag.fetch_links(html, '' if 'auth' not in params else authSession)

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
            linksFound = filterURL(page.fetch_links("", '' if 'auth' not in params else authSession), URL)
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

    # GB
    if 'e' in params and params['e']=='gb':
        links = {
        'https://www.edwards.com/gb/3D-Rotator-Responsive',
        'https://www.edwards.com/gb/aboutus',
        'https://www.edwards.com/gb/about-us',
        'https://www.edwards.com/gb/aboutus/aboutus/home-2',
        'https://www.edwards.com/gb/aboutus/aboutus/temp',
        'https://www.edwards.com/gb/aboutus/aboutus/thv-video',
        'https://www.edwards.com/gb/aboutus/accesshealthcare',
        'https://www.edwards.com/gb/aboutus/au-home',
        'https://www.edwards.com/gb/aboutus/clinicaled',
        'https://www.edwards.com/gb/aboutus/clinical-education-support',
        'https://www.edwards.com/gb/aboutus/codefinder',
        'https://www.edwards.com/gb/aboutus/contactus',
        'https://www.edwards.com/gb/aboutus/contactus2',
        'https://www.edwards.com/gb/aboutus/contactusgeneral',
        'https://www.edwards.com/gb/aboutus/contactusimage',
        'https://www.edwards.com/gb/aboutus/ContactUsPage',
        'https://www.edwards.com/gb/aboutus/contactuspatient',
        'https://www.edwards.com/gb/aboutus/contactusproduct',
        'https://www.edwards.com/gb/aboutus/contactusproductother',
        'https://www.edwards.com/gb/aboutus/corporategiving',
        'https://www.edwards.com/gb/aboutus/corp-responsibility',
        'https://www.edwards.com/gb/aboutus/credo',
        'https://www.edwards.com/gb/aboutus/ecommerce',
        'https://www.edwards.com/gb/aboutus/edi',
        'https://www.edwards.com/gb/aboutus/employeevolunteer',
        'https://www.edwards.com/gb/aboutus/Europe-EMS-Policy',
        'https://www.edwards.com/gb/aboutus/events',
        'https://www.edwards.com/gb/aboutus/events-2',
        'https://www.edwards.com/gb/aboutus/ewproducts',
        'https://www.edwards.com/gb/aboutus/global-giving-objectives',
        'https://www.edwards.com/gb/aboutus/globallocations',
        'https://www.edwards.com/gb/aboutus/global-locations',
        'https://www.edwards.com/gb/aboutus/heartbeat',
        'https://www.edwards.com/gb/aboutus/heartbeat-2',
        'https://www.edwards.com/gb/aboutus/History',
        'https://www.edwards.com/gb/aboutus/home',
        'https://www.edwards.com/gb/aboutus/matchinggift',
        'https://www.edwards.com/gb/aboutus/news',
        'https://www.edwards.com/gb/aboutus/news-releases',
        'https://www.edwards.com/gb/aboutus/newsroom',
        'https://www.edwards.com/gb/aboutus/OurHistory',
        'https://www.edwards.com/gb/aboutus/ourleaders',
        'https://www.edwards.com/gb/aboutus/pastgrant',
        'https://www.edwards.com/gb/aboutus/patientday',
        'https://www.edwards.com/gb/aboutus/patientprograms',
        'https://www.edwards.com/gb/aboutus/patientstories',
        'https://www.edwards.com/gb/aboutus/patientvoice',
        'https://www.edwards.com/gb/aboutus/PCORI',
        'https://www.edwards.com/gb/aboutus/philanthropy',
        'https://www.edwards.com/gb/aboutus/physiciansfinance',
        'https://www.edwards.com/gb/aboutus/policymakers',
        'https://www.edwards.com/gb/aboutus/PoliticalDisclosure',
        'https://www.edwards.com/gb/aboutus/products',
        'https://www.edwards.com/gb/aboutus/products-2',
        'https://www.edwards.com/gb/aboutus/reimbursement',
        'https://www.edwards.com/gb/aboutus/reimbursementassist',
        'https://www.edwards.com/gb/aboutus/romanian-financial-relationships',
        'https://www.edwards.com/gb/aboutus/testerjosh',
        'https://www.edwards.com/gb/aboutus/what-we-do',
        'https://www.edwards.com/gb/about-us_old',
        'https://www.edwards.com/gb/about-us-prototype',
        'https://www.edwards.com/gb/Accessories',
        'https://www.edwards.com/gb/accessories/Vascushunt-II-Silicone-Carotid-Shunt',
        'https://www.edwards.com/gb/accessories/Vascushunt-II-Silicone-Carotid-Shunt-2',
        'https://www.edwards.com/gb/accordionsample',
        'https://www.edwards.com/gb/advanced-hemodynamic-monitoring',
        'https://www.edwards.com/gb/AnnuloplastyRings',
        'https://www.edwards.com/gb/AnnuloplastyRings/devices/annuloplasty/mitral',
        'https://www.edwards.com/gb/AnnuloplastyRings/devices/annuloplasty/mitral-heart-valve-repair',
        'https://www.edwards.com/gb/AnnuloplastyRings/mc3tricuspid',
        'https://www.edwards.com/gb/AnnuloplastyRings/mitral-valve-repair-portfolio',
        'https://www.edwards.com/gb/AnnuloplastyRings/PhysioTricuspidTest',
        'https://www.edwards.com/gb/aortic-valve-portfolio',
        'https://www.edwards.com/gb/ask-a-question',
        'https://www.edwards.com/gb/ask-a-question-2',
        'https://www.edwards.com/gb/auto-play',
        'https://www.edwards.com/gb/auto-play-videos',
        'https://www.edwards.com/gb/auto-play-videos',
        'https://www.edwards.com/gb/banner-testing',
        'https://www.edwards.com/gb/BloodManagement',
        'https://www.edwards.com/gb/bloodmanagementforms',
        'https://www.edwards.com/gb/bms-page',
        'https://www.edwards.com/gb/caqreerscontactus',
        'https://www.edwards.com/gb/cardiobandmitralsystem',
        'https://www.edwards.com/gb/CardiobandTR',
        'https://www.edwards.com/gb/cardiobandtricuspidsystem',
        'https://www.edwards.com/gb/careers',
        'https://www.edwards.com/gb/careers/agencies',
        'https://www.edwards.com/gb/careers/askaquestion',
        'https://www.edwards.com/gb/careers/ask-a-question',
        'https://www.edwards.com/gb/careers/benefits',
        'https://www.edwards.com/gb/careers/developmentprograms',
        'https://www.edwards.com/gb/careers/diversity',
        'https://www.edwards.com/gb/careers/diversity-and-inclusion',
        'https://www.edwards.com/gb/careers/diversity-inclusion',
        'https://www.edwards.com/gb/careers/employeebenefits',
        'https://www.edwards.com/gb/careers/ENGWeekend',
        'https://www.edwards.com/gb/careers/faqs',
        'https://www.edwards.com/gb/careers/financedevelopmentprogram',
        'https://www.edwards.com/gb/careers/home',
        'https://www.edwards.com/gb/careers/internships',
        'https://www.edwards.com/gb/careers/jobs',
        'https://www.edwards.com/gb/careers/locations',
        'https://www.edwards.com/gb/careers/Meet-Our-Employees',
        'https://www.edwards.com/gb/careers/our-culture',
        'https://www.edwards.com/gb/careers/professionalareas',
        'https://www.edwards.com/gb/careers/professional-development',
        'https://www.edwards.com/gb/careers/questions',
        'https://www.edwards.com/gb/careers/recruitingcalender',
        'https://www.edwards.com/gb/careers/searchjobs',
        'https://www.edwards.com/gb/careers/tdp',
        'https://www.edwards.com/gb/careers/universityengineeringprogram',
        'https://www.edwards.com/gb/careers/universityrecruiting',
        'https://www.edwards.com/gb/careers/universitysummerprogram',
        'https://www.edwards.com/gb/careers/workinghere',
        'https://www.edwards.com/gb/careerscontactus',
        'https://www.edwards.com/gb/catagorypickersalesrep',
        'https://www.edwards.com/gb/Catheters',
        'https://www.edwards.com/gb/Catheters/AtraumaticOcclusion',
        'https://www.edwards.com/gb/Catheters/balloon-carotid-shunts',
        'https://www.edwards.com/gb/Catheters/carotid-shunts',
        'https://www.edwards.com/gb/Catheters/ClotManagement',
        'https://www.edwards.com/gb/Catheters/clot-management',
        'https://www.edwards.com/gb/Catheters/devices/Catheters/Arterial_Cannulae',
        'https://www.edwards.com/gb/Catheters/devices/Catheters/ArterialCannulae',
        'https://www.edwards.com/gb/Catheters/general-surgery',
        'https://www.edwards.com/gb/Catheters/general-surgery-balloon-atrioseptostomy',
        'https://www.edwards.com/gb/Catheters/occlusion',
        'https://www.edwards.com/gb/Catheters/OtherVascularSurgery',
        'https://www.edwards.com/gb/Catheters/VascularBiliarySurgery',
        'https://www.edwards.com/gb/Catheters/Vascular-Biliary-Surgery',
        'https://www.edwards.com/gb/cc-contact-sales-rep',
        'https://www.edwards.com/gb/cc-contact-us-form',
        'https://www.edwards.com/gb/CCeducationForm',
        'https://www.edwards.com/gb/cc-education-form',
        'https://www.edwards.com/gb/ccpreferancecenter',
        'https://www.edwards.com/gb/CCSubscriptionCenter',
        'https://www.edwards.com/gb/channels',
        'https://www.edwards.com/gb/clinicaleducation',
        'https://www.edwards.com/gb/codefinder',
        'https://www.edwards.com/gb/codelookup',
        'https://www.edwards.com/gb/code-lookup-widget',
        'https://www.edwards.com/gb/company-info-request',
        'https://www.edwards.com/gb/contactrepvascular',
        'https://www.edwards.com/gb/ContactSales',
        'https://www.edwards.com/gb/contact-us',
        'https://www.edwards.com/gb/contact-us-form',
        'https://www.edwards.com/gb/contact-us-form-2',
        'https://www.edwards.com/gb/contactusimage',
        'https://www.edwards.com/gb/contactusproducthvt',
        'https://www.edwards.com/gb/contactusproductthv',
        'https://www.edwards.com/gb/content-deployment',
        'https://www.edwards.com/gb/cookie-statement',
        'https://www.edwards.com/gb/cookie-statement',
        'https://www.edwards.com/gb/corporategiving',
        'https://www.edwards.com/gb/corporate-giving',
        'https://www.edwards.com/gb/corporate-responsibility',
        'https://www.edwards.com/gb/corp-responsibility',
        'https://www.edwards.com/gb/correct-change-personal-information',
        'https://www.edwards.com/gb/credo',
        'https://www.edwards.com/gb/Critical-Care-Subscription-Center',
        'https://www.edwards.com/gb/Critical-Care-Subscription-Center-Mod',
        'https://www.edwards.com/gb/Critical-Care-Subscription-Center-Unsub',
        'https://www.edwards.com/gb/device-categories-Vascular-Products',
        'https://www.edwards.com/gb/devices',
        'https://www.edwards.com/gb/devices/Accessories/Atraumatic-Occlusion',
        'https://www.edwards.com/gb/devices/Accessories/carotid-shunts',
        'https://www.edwards.com/gb/devices/accessories/Minimal-Incision-MVR-AVR',
        'https://www.edwards.com/gb/devices/accessories/MVR',
        'https://www.edwards.com/gb/devices/annuloplasty/mitral',
        'https://www.edwards.com/gb/devices/annuloplasty/mitral-heart-valve-repair',
        'https://www.edwards.com/gb/devices/annuloplasty/mitral-valve-repair',
        'https://www.edwards.com/gb/devices/annuloplasty/tricuspid',
        'https://www.edwards.com/gb/devices/annuloplasty/tricuspid-heart-valve-repair',
        'https://www.edwards.com/gb/devices/Catheters/ArterialCannulae',
        'https://www.edwards.com/gb/devices/Catheters/Arterial-Cannulae',
        'https://www.edwards.com/gb/devices/Catheters/AtraumaticOcclusion',
        'https://www.edwards.com/gb/devices/Catheters/Atraumatic-Occlusion',
        'https://www.edwards.com/gb/devices/Catheters/carotid-shunts',
        'https://www.edwards.com/gb/Devices/Catheters/ClotManagement',
        'https://www.edwards.com/gb/Devices/Catheters/Clot-Management',
        'https://www.edwards.com/gb/devices/Catheters/general-surgery',
        'https://www.edwards.com/gb/devices/catheters/MVR',
        'https://www.edwards.com/gb/devices/Catheters/occlusion',
        'https://www.edwards.com/gb/devices/Catheters/Other-Vascular',
        'https://www.edwards.com/gb/devices/Catheters/Vascular',
        'https://www.edwards.com/gb/devices/Catheters/Vascular-2',
        'https://www.edwards.com/gb/devices/central-venous-access/ava-3xi',
        'https://www.edwards.com/gb/devices/central-venous-access/ava-high-flow',
        'https://www.edwards.com/gb/devices/decision-software/afm',
        'https://www.edwards.com/gb/devices/decision-software/hpi',
        'https://www.edwards.com/gb/devices/device_categories_Vascular_Products',
        'https://www.edwards.com/gb/devices/device-categories',
        'https://www.edwards.com/gb/devices/device-categories-Vascular-Products',
        'https://www.edwards.com/gb/devices/device-categories-Vascular-Products-2',
        'https://www.edwards.com/gb/devices/devices/mivsproductcategory-2',
        'https://www.edwards.com/gb/devices/edwards-sapien-3-transcatheter-heart-valve',
        'https://www.edwards.com/gb/devices/ESRPage',
        'https://www.edwards.com/gb/devices/evictoutput',
        'https://www.edwards.com/gb/devices/heartvalves',
        'https://www.edwards.com/gb/devices/heartvalves/aortic',
        'https://www.edwards.com/gb/devices/heart-valves/aortic-pericardial',
        'https://www.edwards.com/gb/devices/heartvalves/AORTICVALVEPORTFOLIO',
        'https://www.edwards.com/gb/devices/Heart-Valves/CENTERA',
        'https://www.edwards.com/gb/devices/heartvalves/devices/heartvalves/mitral-2',
        'https://www.edwards.com/gb/devices/heartvalves/devices/heart-valves/transcatheter-sapien-xt-viv',
        'https://www.edwards.com/gb/devices/heart-valves/intuity',
        'https://www.edwards.com/gb/devices/heartvalves/josh',
        'https://www.edwards.com/gb/devices/heartvalves/magnaease',
        'https://www.edwards.com/gb/devices/heartvalves/mitral',
        'https://www.edwards.com/gb/devices/heart-valves/mitral',
        'https://www.edwards.com/gb/devices/heartvalves/mitral2',
        'https://www.edwards.com/gb/devices/heartvalves/MVR',
        'https://www.edwards.com/gb/devices/heartvalves/operator',
        'https://www.edwards.com/gb/devices/heart-valves/resilia',
        'https://www.edwards.com/gb/devices/heartvalves/sapien3-transcatheter',
        'https://www.edwards.com/gb/devices/heartvalves/sapienxt',
        'https://www.edwards.com/gb/devices/heart-valves/sapien-xt-transcatheter',
        'https://www.edwards.com/gb/devices/heart-valves/sapien-xt-valve',
        'https://www.edwards.com/gb/devices/heartvalves/sapien-xt-valve-in-valve',
        'https://www.edwards.com/gb/devices/heart-valves/sapien-xt-valve-in-valve',
        'https://www.edwards.com/gb/devices/heart-valves/surgical-valve-technologies',
        'https://www.edwards.com/gb/devices/heartvalves/TestMagnaEase',
        'https://www.edwards.com/gb/devices/heartvalves/test-training',
        'https://www.edwards.com/gb/devices/heartvalves/transcatheter',
        'https://www.edwards.com/gb/devices/heart-valves/transcatheter',
        'https://www.edwards.com/gb/devices/heartvalves/transcatheter-heart-valves',
        'https://www.edwards.com/gb/devices/Heart-Valves/Transcatheter-Sapien-3',
        'https://www.edwards.com/gb/devices/heart-valves/transcatheter-SAPIEN-3-Ultra',
        'https://www.edwards.com/gb/devices/heart-valves/transcatheter-sapien-pulmonic',
        'https://www.edwards.com/gb/devices/heart-valves/transcatheter-sapien-xt',
        'https://www.edwards.com/gb/devices/heart-valves/transcatheter-sapien-xt-valve-pulmonic',
        'https://www.edwards.com/gb/devices/heartvalves/xvrsapienxt',
        'https://www.edwards.com/gb/devices/hemodynamic-monitoring',
        'https://www.edwards.com/gb/devices/hemodynamic-monitoring/acumen-analytics',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/clearsight',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/EV1000',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/EV1000-Clinical-Platform',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/FloTrac',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/FloTracsampleform',
        'https://www.edwards.com/gb/devices/hemodynamic-monitoring/hemosphere',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/InstrumentSystems',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/Monitoring-Platforms',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/Oximetry-Central-Venous-Catheter',
        'https://www.edwards.com/gb/Devices/Hemodynamic-Monitoring/PediaSat-Catheter',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/PreSep-Oximetry-Catheter',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/swan-ganz-catheters',
        'https://www.edwards.com/gb/devices/hemodynamic-monitoring/systems',
        'https://www.edwards.com/gb/devices/hemodynamic-monitoring/tissue-oximetry',
        'https://www.edwards.com/gb/devices/hemodynamic-monitoring/tissue-oximetry/thankyou',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/VigilanceII',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/Vigilance-II-Monitor',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/Vigileo',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/Vigileo-Monitor',
        'https://www.edwards.com/gb/devices/Hemodynamic-Monitoring/VolumeView',
        'https://www.edwards.com/gb/devices/home',
        'https://www.edwards.com/gb/devices/mivsproductcategory',
        'https://www.edwards.com/gb/devices/mivsproductcategory-2',
        'https://www.edwards.com/gb/devices/Monitoring/clearsight',
        'https://www.edwards.com/gb/devices/Monitoring/FloTrac',
        'https://www.edwards.com/gb/devices/Monitoring/Monitoring/clearsight',
        'https://www.edwards.com/gb/Devices/Monitoring/PediaSat',
        'https://www.edwards.com/gb/devices/Monitoring/swanganz',
        'https://www.edwards.com/gb/devices/Pressure-Monitoring/Closed-Blood-Sampling',
        'https://www.edwards.com/gb/devices/Pressure-Monitoring/Transducer',
        'https://www.edwards.com/gb/devices/Pressure-Monitoring/truclip-holder',
        'https://www.edwards.com/gb/devices/Pressure-Monitoring/truclip-holder-bakcup',
        'https://www.edwards.com/gb/devices/systems',
        'https://www.edwards.com/gb/devices/transcatheter-valve-repair/cardiobandmitralsystem',
        'https://www.edwards.com/gb/devices/transcatheter-valve-repair/cardiobandtricuspidsystem',
        'https://www.edwards.com/gb/devices/transcatheter-valve-repair/PASCAL',
        'https://www.edwards.com/gb/devices/Vascular',
        'https://www.edwards.com/gb/devices/Vascular-Products',
        'https://www.edwards.com/gb/devices/xavortest',
        'https://www.edwards.com/gb/devices-2',
        'https://www.edwards.com/gb/diversity',
        'https://www.edwards.com/gb/diversity-and-inclusion',
        'https://www.edwards.com/gb/diversity-inclusion',
        'https://www.edwards.com/gb/download-pgdt-analytics',
        'https://www.edwards.com/gb/dummypage',
        'https://www.edwards.com/gb/ECCE-webinar',
        'https://www.edwards.com/gb/education',
        'https://www.edwards.com/gb/education/blood-conservation-interactive-learning',
        'https://www.edwards.com/gb/education/ecce',
        'https://www.edwards.com/gb/education/heart-valve-therapies',
        'https://www.edwards.com/gb/education/volume-administration-interactive-learning',
        'https://www.edwards.com/gb/educationcategory',
        'https://www.edwards.com/gb/educationcategory/animations-videos',
        'https://www.edwards.com/gb/educationcategory/elearning-modules',
        'https://www.edwards.com/gb/educationcategory/events',
        'https://www.edwards.com/gb/educationcategory/external-links',
        'https://www.edwards.com/gb/educationcategory/general-reference',
        'https://www.edwards.com/gb/educationcategory/interactive',
        'https://www.edwards.com/gb/educationcategory/presentations',
        'https://www.edwards.com/gb/educationcategory/webinars',
        'https://www.edwards.com/gb/educationcategory/white-papers',
        'https://www.edwards.com/gb/education-demo-page',
        'https://www.edwards.com/gb/education-demo-product-page-with-categories',
        'https://www.edwards.com/gb/educationdocumentcategory',
        'https://www.edwards.com/gb/educationdocumenttopic',
        'https://www.edwards.com/gb/educationdocumenttopic/conditions',
        'https://www.edwards.com/gb/educationdocumenttopic/devices',
        'https://www.edwards.com/gb/educationdocumenttopic/devices/accessories-and-instruments',
        'https://www.edwards.com/gb/educationdocumenttopic/devices/annuloplasty-rings',
        'https://www.edwards.com/gb/educationdocumenttopic/devices/annuloplasty-rings/mitral-repair',
        'https://www.edwards.com/gb/educationdocumenttopic/devices/annuloplasty-rings/tricuspid-repair',
        'https://www.edwards.com/gb/educationdocumenttopic/devices/catheters',
        'https://www.edwards.com/gb/educationdocumenttopic/devices/heart-valves',
        'https://www.edwards.com/gb/educationdocumenttopic/devices/monitoring',
        'https://www.edwards.com/gb/educationdocumenttopic/specialty-teams',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/blood-conservation',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/clot-management',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/coronary-artery-bypass',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/enhanced-surgical-recovery',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/heart-valve-repair',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/infection-control',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/minimal-incision-surgery',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/shock-and-sepsis-management',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/surgical-heart-valve-replacement',
        'https://www.edwards.com/gb/educationdocumenttopic/therapies/tavr',
        'https://www.edwards.com/gb/educationdocumenttype',
        'https://www.edwards.com/gb/educationdocumenttype/case-studies',
        'https://www.edwards.com/gb/educationdocumenttype/instructions-for-use',
        'https://www.edwards.com/gb/educationdocumenttype/manuals',
        'https://www.edwards.com/gb/educationdocumenttype/white-papers',
        'https://www.edwards.com/gb/educationproduct',
        'https://www.edwards.com/gb/educationproduct/clearsight-system',
        'https://www.edwards.com/gb/educationproduct/ev1000',
        'https://www.edwards.com/gb/educationproduct/flotrac-sensor',
        'https://www.edwards.com/gb/educationproduct/mivs',
        'https://www.edwards.com/gb/educationproduct/monitoring-platforms',
        'https://www.edwards.com/gb/educationproduct/presep-pediasat',
        'https://www.edwards.com/gb/educationproduct/swan-ganz-catheters',
        'https://www.edwards.com/gb/educationproduct/truwave',
        'https://www.edwards.com/gb/educationproduct/vamp-system',
        'https://www.edwards.com/gb/educationproduct/volumeview-set',
        'https://www.edwards.com/gb/edwards-lifesciences-the-leader-in-heart-valves-hemodynamic-monitoring',
        'https://www.edwards.com/gb/edwards-lunch-symposium-the-esicm-lives-congress-2015',
        'https://www.edwards.com/gb/ehm-guidelines-and-reporting-obligations',
        'https://www.edwards.com/gb/e-learning-hemodynamic-monitoring',
        'https://www.edwards.com/gb/employeebenefits',
        'https://www.edwards.com/gb/empty-alts',
        'https://www.edwards.com/gb/ENGWeekend',
        'https://www.edwards.com/gb/eng-weekend-fall-2015',
        'https://www.edwards.com/gb/enhanced-surgical-recovery',
        'https://www.edwards.com/gb/enhanced-surgical-recovery-2',
        'https://www.edwards.com/gb/ESICM2016',
        'https://www.edwards.com/gb/ESICM2016',
        'https://www.edwards.com/gb/ESICM2017',
        'https://www.edwards.com/gb/ESR',
        'https://www.edwards.com/gb/esr',
        'https://www.edwards.com/gb/ESR-Microsite',
        'https://www.edwards.com/gb/ESR-Microsite-2',
        'https://www.edwards.com/gb/ESRPage',
        'https://www.edwards.com/gb/esr-page',
        'https://www.edwards.com/gb/esrpage-eu',
        'https://www.edwards.com/gb/esr-sample',
        'https://www.edwards.com/gb/esr-solution-page',
        'https://www.edwards.com/gb/esr-test',
        'https://www.edwards.com/gb/eu/edwards-lunch-symposium-the-esicm-lives-congress-2015',
        'https://www.edwards.com/gb/events',
        'https://www.edwards.com/gb/events-2',
        'https://www.edwards.com/gb/events-3',
        'https://www.edwards.com/gb/evictoutput',
        'https://www.edwards.com/gb/feasefasef',
        'https://www.edwards.com/gb/financial-relationships-with-romanian-physicians',
        'https://www.edwards.com/gb/find-a-tavr-sample-page',
        'https://www.edwards.com/gb/find-tavr-html',
        'https://www.edwards.com/gb/fonts-egel',
        'https://www.edwards.com/gb/form',
        'https://www.edwards.com/gb/forms/cc-contact-us-form',
        'https://www.edwards.com/gb/forms/productcategorypicker',
        'https://www.edwards.com/gb/forms/request-a-copy-of-sepsis-bundle-guidelines-overview',
        'https://www.edwards.com/gb/forms/sepsis-general-request',
        'https://www.edwards.com/gb/forms/sepsis-general-request',
        'https://www.edwards.com/gb/formtest',
        'https://www.edwards.com/gb/FormVascular',
        'https://www.edwards.com/gb/generictemplate',
        'https://www.edwards.com/gb/googlebc21efd97457f40c',
        'https://www.edwards.com/gb/harpoonmedical',
        'https://www.edwards.com/gb/HCPS',
        'https://www.edwards.com/gb/hcp-solutions',
        'https://www.edwards.com/gb/heart-team',
        'https://www.edwards.com/gb/heart-valve-2',
        'https://www.edwards.com/gb/Heart-Valves/Transcatheter-Sapien-3',
        'https://www.edwards.com/gb/heart-valve-therapies',
        'https://www.edwards.com/gb/HELP',
        'https://www.edwards.com/gb/hemodynamic-monitoring',
        'https://www.edwards.com/gb/Hemodynamic-Monitoring/PreSep',
        'https://www.edwards.com/gb/Hemodynamic-Monitoring/PreSep-Oximetry-Catheter',
        'https://www.edwards.com/gb/Hemodynamic-Monitoring/VigilanceII',
        'https://www.edwards.com/gb/Hemodynamic-Monitoring/VigilanceII',
        'https://www.edwards.com/gb/Hemodynamic-Monitoring/VolumeView',
        'https://www.edwards.com/gb/History',
        'https://www.edwards.com/gb/homepagebannerwidget',
        'https://www.edwards.com/gb/hvt-education-product',
        'https://www.edwards.com/gb/hvt-education-product/mivs',
        'https://www.edwards.com/gb/img-responsive',
        'https://www.edwards.com/gb/investors',
        'https://www.edwards.com/gb/investors/home',
        'https://www.edwards.com/gb/isicem2019/Early-Resuscitation-in-Sepsis-Report',
        'https://www.edwards.com/gb/isicem2019/Evaluating-Volemic-Status-Report',
        'https://www.edwards.com/gb/isicem2019/Hemodynamic-Monitoring-Report',
        'https://www.edwards.com/gb/isicem2019/How-I-See-the-Future-Report',
        'https://www.edwards.com/gb/isicem2019/Optimizing-Perioperative-Care-Report',
        'https://www.edwards.com/gb/isicem2019/Reports',
        'https://www.edwards.com/gb/jobs',
        'https://www.edwards.com/gb/joshtesters',
        'https://www.edwards.com/gb/learnmorehdm',
        'https://www.edwards.com/gb/legal/legalterms',
        'https://www.edwards.com/gb/legal/privacypolicy',
        'https://www.edwards.com/gb/legal-terms',
        'https://www.edwards.com/gb/let-s-purge-2',
        'https://www.edwards.com/gb/locations',
        'https://www.edwards.com/gb/mc3tricuspid',
        'https://www.edwards.com/gb/mediaslider',
        'https://www.edwards.com/gb/media-slider-changes-test-page',
        'https://www.edwards.com/gb/microsite-esr',
        'https://www.edwards.com/gb/minimal-incision-valve-surgery',
        'https://www.edwards.com/gb/minimal-incision-valve-surgery-2',
        'https://www.edwards.com/gb/mitral-test',
        'https://www.edwards.com/gb/mitral-valve-repair-portfolio',
        'https://www.edwards.com/gb/MIVS',
        'https://www.edwards.com/gb/Monitoring',
        'https://www.edwards.com/gb/Monitoring/clearsight',
        'https://www.edwards.com/gb/Monitoring/ClosedBloodSampling',
        'https://www.edwards.com/gb/Monitoring/devices/Hemodynamic-Monitoring/FloTrac',
        'https://www.edwards.com/gb/Monitoring/devices/Hemodynamic-Monitoring/PreSep-Oximetry-Catheter-Clone',
        'https://www.edwards.com/gb/Monitoring/devices/Monitoring/clearsight',
        'https://www.edwards.com/gb/Monitoring/devices/Monitoring/FloTrac',
        'https://www.edwards.com/gb/Monitoring/devices/Monitoring/swanganz-1',
        'https://www.edwards.com/gb/Monitoring/devices/Monitoring/swanganz-222',
        'https://www.edwards.com/gb/Monitoring/FloTrac',
        'https://www.edwards.com/gb/Monitoring/hemodynamic-monitoring',
        'https://www.edwards.com/gb/Monitoring/Monitoring/clearsight-2',
        'https://www.edwards.com/gb/Monitoring/PediaSat',
        'https://www.edwards.com/gb/Monitoring/PreSep',
        'https://www.edwards.com/gb/Monitoring/PressureMonitoring',
        'https://www.edwards.com/gb/Monitoring/swan-ganz-catheters',
        'https://www.edwards.com/gb/Monitoring/truclip-holder',
        'https://www.edwards.com/gb/Monitoring/VolumeView',
        'https://www.edwards.com/gb/mri-safety',
        'https://www.edwards.com/gb/multi-banner',
        'https://www.edwards.com/gb/mvm2018',
        'https://www.edwards.com/gb/newheartvalve-com-care-giver-heart-team-circle',
        'https://www.edwards.com/gb/newheartvalve-com-care-giver-heart-team-circle-2',
        'https://www.edwards.com/gb/or-solutions-contact-sales',
        'https://www.edwards.com/gb/pagebannerwidget',
        'https://www.edwards.com/gb/passcode',
        'https://www.edwards.com/gb/patient/heartvalve',
        'https://www.edwards.com/gb/patient-info-request',
        'https://www.edwards.com/gb/patientprograms',
        'https://www.edwards.com/gb/patients',
        'https://www.edwards.com/gb/patients/faq',
        'https://www.edwards.com/gb/patients/glossary',
        'https://www.edwards.com/gb/patients/heartvalve',
        'https://www.edwards.com/gb/patients/heart-valve',
        'https://www.edwards.com/gb/patients/implantpatientregistry',
        'https://www.edwards.com/gb/patients/josh-patients',
        'https://www.edwards.com/gb/patients/patient-information',
        'https://www.edwards.com/gb/patientvoice',
        'https://www.edwards.com/gb/patientvoiceform',
        'https://www.edwards.com/gb/PCORI',
        'https://www.edwards.com/gb/pericardial-heart-valves/bovine-pericardial-patch',
        'https://www.edwards.com/gb/PhysioTricuspidTest',
        'https://www.edwards.com/gb/picyourbu',
        'https://www.edwards.com/gb/piek3contact',
        'https://www.edwards.com/gb/policymakers',
        'https://www.edwards.com/gb/popups',
        'https://www.edwards.com/gb/preferancecenter',
        'https://www.edwards.com/gb/preferancecenterpage2',
        'https://www.edwards.com/gb/preferencecenter',
        'https://www.edwards.com/gb/preference-center-cc',
        'https://www.edwards.com/gb/preferencecenterpage2',
        'https://www.edwards.com/gb/Pressure-Monitoring/Closed-Blood-Sampling',
        'https://www.edwards.com/gb/Pressure-Monitoring/Transducer',
        'https://www.edwards.com/gb/Pressure-Monitoring/truclip-holder',
        'https://www.edwards.com/gb/privacy-policy',
        'https://www.edwards.com/gb/procedures/aorticstenosis/awareness',
        'https://www.edwards.com/gb/procedures/aorticstenosis/evaluation',
        'https://www.edwards.com/gb/procedures/aorticstenosis/guidelines',
        'https://www.edwards.com/gb/procedures/aorticstenosis/options',
        'https://www.edwards.com/gb/procedures/aorticstenosis/partner',
        'https://www.edwards.com/gb/procedures/aorticstenosis/prevalence',
        'https://www.edwards.com/gb/procedures/aorticstenosis/progression',
        'https://www.edwards.com/gb/procedures/aorticstenosis/referral',
        'https://www.edwards.com/gb/procedures/aorticstenosis/results',
        'https://www.edwards.com/gb/procedures/aorticstenosis/standard',
        'https://www.edwards.com/gb/product-category-picker-rep-visit',
        'https://www.edwards.com/gb/product-information-and-support-request-form',
        'https://www.edwards.com/gb/products',
        'https://www.edwards.com/gb/purge-dummy',
        'https://www.edwards.com/gb/purge-test',
        'https://www.edwards.com/gb/purgworktest3',
        'https://www.edwards.com/gb/questions-concerns-about-personal-information',
        'https://www.edwards.com/gb/redirect',
        'https://www.edwards.com/gb/remove-info-under-age-13',
        'https://www.edwards.com/gb/remove-personal-information',
        'https://www.edwards.com/gb/request-a-copy-of-sepsis-bundle-guidelines-overview',
        'https://www.edwards.com/gb/request-product-image',
        'https://www.edwards.com/gb/rics-garbage-form',
        'https://www.edwards.com/gb/ric-s-testing-page-do-not-remove',
        'https://www.edwards.com/gb/riskinformation',
        'https://www.edwards.com/gb/romanian-financial-relationships',
        'https://www.edwards.com/gb/Sapian3',
        'https://www.edwards.com/gb/Sapien-3',
        'https://www.edwards.com/gb/Sapien3-1',
        'https://www.edwards.com/gb/sapien3-test',
        'https://www.edwards.com/gb/sepsis-management',
        'https://www.edwards.com/gb/sepsis-management-2',
        'https://www.edwards.com/gb/setupdemo',
        'https://www.edwards.com/gb/site-leaving-warning',
        'https://www.edwards.com/gb/social-icon-demo',
        'https://www.edwards.com/gb/specialityteams',
        'https://www.edwards.com/gb/specialityteams/transcatheter-aortic-heart-valve-tavr-heart-team',
        'https://www.edwards.com/gb/specialtyteams',
        'https://www.edwards.com/gb/specialtyteams/hcp-solutions',
        'https://www.edwards.com/gb/specialty-teams/HCP-Solutions',
        'https://www.edwards.com/gb/specialtyteams/heart-team',
        'https://www.edwards.com/gb/specialty-teams/heart-team',
        'https://www.edwards.com/gb/specialtyteams/hospital-administration/hcp-solutions',
        'https://www.edwards.com/gb/specialty-teams/ICU-Solutions',
        'https://www.edwards.com/gb/specialtyteams/TAVR',
        'https://www.edwards.com/gb/specialtyteams/TAVR/TAVR-Sample',
        'https://www.edwards.com/gb/specialtyteams/Vascular-team',
        'https://www.edwards.com/gb/stoptest',
        'https://www.edwards.com/gb/surgical-heart-valves',
        'https://www.edwards.com/gb/systems',
        'https://www.edwards.com/gb/SystemsProducts',
        'https://www.edwards.com/gb/TAVR-Sample',
        'https://www.edwards.com/gb/temp5',
        'https://www.edwards.com/gb/template-for-outsourcing',
        'https://www.edwards.com/gb/test',
        'https://www.edwards.com/gb/test',
        'https://www.edwards.com/gb/test-2',
        'https://www.edwards.com/gb/test-3',
        'https://www.edwards.com/gb/test425',
        'https://www.edwards.com/gb/testazureheavy',
        'https://www.edwards.com/gb/testazurerecipe',
        'https://www.edwards.com/gb/test-banner',
        'https://www.edwards.com/gb/testcanonical',
        'https://www.edwards.com/gb/testcn',
        'https://www.edwards.com/gb/test-content-accordion',
        'https://www.edwards.com/gb/testcredo',
        'https://www.edwards.com/gb/test-device-for-tabslider-position',
        'https://www.edwards.com/gb/testerjosh',
        'https://www.edwards.com/gb/test-event',
        'https://www.edwards.com/gb/test-frameless',
        'https://www.edwards.com/gb/testing-for-accordion-issue',
        'https://www.edwards.com/gb/testjumpslider',
        'https://www.edwards.com/gb/test-media-slider',
        'https://www.edwards.com/gb/test-microsite',
        'https://www.edwards.com/gb/test-multi-banner',
        'https://www.edwards.com/gb/testoverlaycontent',
        'https://www.edwards.com/gb/test-page',
        'https://www.edwards.com/gb/test-page-2',
        'https://www.edwards.com/gb/testprod',
        'https://www.edwards.com/gb/testpurgworkflow',
        'https://www.edwards.com/gb/testpurgworkflow2',
        'https://www.edwards.com/gb/testRisk',
        'https://www.edwards.com/gb/testslideshow',
        'https://www.edwards.com/gb/test-tab-slider',
        'https://www.edwards.com/gb/test-tab-slider-page',
        'https://www.edwards.com/gb/test-taxonomy',
        'https://www.edwards.com/gb/test-theripes',
        'https://www.edwards.com/gb/testuseast',
        'https://www.edwards.com/gb/textfixurl',
        'https://www.edwards.com/gb/therapies',
        'https://www.edwards.com/gb/therapies/Blood-Conservation',
        'https://www.edwards.com/gb/therapies/Blood-Conservation-1',
        'https://www.edwards.com/gb/Therapies/BloodManagement',
        'https://www.edwards.com/gb/therapies/enhanced-surgical-recovery',
        'https://www.edwards.com/gb/therapies/enhanced-surgical-recovery-1',
        'https://www.edwards.com/gb/therapies/enhanced-surgical-recovery-2',
        'https://www.edwards.com/gb/therapies/ESR',
        'https://www.edwards.com/gb/therapies/fluid-management',
        'https://www.edwards.com/gb/therapies/hypotension-management',
        'https://www.edwards.com/gb/therapies/minimal-incision-valve-surgery',
        'https://www.edwards.com/gb/therapies/minimal-incision-valve-surgery-2',
        'https://www.edwards.com/gb/therapies/MIVS',
        'https://www.edwards.com/gb/therapies/MIVS2',
        'https://www.edwards.com/gb/therapies/MIVS-2',
        'https://www.edwards.com/gb/therapies/OR-Solutions-for-ESR',
        'https://www.edwards.com/gb/therapies/OR-Solutions-for-ESR-1',
        'https://www.edwards.com/gb/therapies/OR-Solutions-for-ESR2',
        'https://www.edwards.com/gb/therapies/OR-Solutions-for-ESR-g',
        'https://www.edwards.com/gb/therapies/registernow',
        'https://www.edwards.com/gb/therapies/sepsis-management',
        'https://www.edwards.com/gb/therapies/sepsis-managment',
        'https://www.edwards.com/gb/therapies/TAVR',
        'https://www.edwards.com/gb/therapies/therapies/enhanced-surgical-recovery-clone',
        'https://www.edwards.com/gb/therapies/transcatheter-aortic-valve-replacement',
        'https://www.edwards.com/gb/therapies/transcatheter-aortic-valve-replacement-tavr',
        'https://www.edwards.com/gb/this-is-the-generic-type-published-on-qa-and-dev',
        'https://www.edwards.com/gb/this-page-is-to-show-problems-and-new-things-we-want',
        'https://www.edwards.com/gb/thv-customer-travel-reguest',
        'https://www.edwards.com/gb/THV-Customer-Travel-Reguest',
        'https://www.edwards.com/gb/THVCustomerTravelRequest',
        'https://www.edwards.com/gb/THV-Customer-Travel-Request',
        'https://www.edwards.com/gb/thv-customer-travel-request-thank-you',
        'https://www.edwards.com/gb/transcather-aortic-valve-replacement-tavr',
        'https://www.edwards.com/gb/transcatheter',
        'https://www.edwards.com/gb/transcatheter-aortic-heart-valve-tavr-heart-team',
        'https://www.edwards.com/gb/transcatheter-aortic-valve-replacement-tavr',
        'https://www.edwards.com/gb/transcatheter-heart-valves',
        'https://www.edwards.com/gb/transcatheter-sapien-pulmonic',
        'https://www.edwards.com/gb/TrialSolutions',
        'https://www.edwards.com/gb/tricuspidportfolio',
        'https://www.edwards.com/gb/under-construction',
        'https://www.edwards.com/gb/unsub2',
        'https://www.edwards.com/gb/unsubscribe-remove-from-mailing-lists',
        'https://www.edwards.com/gb/valtechcardio',
        'https://www.edwards.com/gb/vascularproduct',
        'https://www.edwards.com/gb/vascular-product',
        'https://www.edwards.com/gb/vascular-products',
        'https://www.edwards.com/gb/vascular-products-2',
        'https://www.edwards.com/gb/vertical-media-slider',
        'https://www.edwards.com/gb/Vigileo',
        'https://www.edwards.com/gb/wsj',
        'https://www.edwards.com/gb/XT-Reimbursement',
        'https://www.edwards.com/gb/xt-reimbursement'
        }
    
    #ch-en
    if 'e' in params and params['e']=='ch-en':
        links = {
        'https://dev.edwards.com/ch-en/aboutus/',
        'https://dev.edwards.com/ch-en/aboutus/contactusgeneral/',
        'https://dev.edwards.com/ch-en/aboutus/corp-responsibility/',
        'https://dev.edwards.com/ch-en/aboutus/employeevolunteer/',
        'https://dev.edwards.com/ch-en/aboutus/europe-ems-policy/',
        'https://dev.edwards.com/ch-en/aboutus/heartbeat/',
        'https://dev.edwards.com/ch-en/aboutus/ehm-guidelines-and-reporting-obligations/',
        'https://dev.edwards.com/ch-en/aboutus/corporategiving/',
        'https://dev.edwards.com/ch-en/aboutus/global-giving-objectives/',
        'https://dev.edwards.com/ch-en/aboutus/pastgrant/',
        'https://dev.edwards.com/ch-en/aboutus/accesshealthcare/',
        'https://dev.edwards.com/ch-en/aboutus/global-locations/',
        'https://dev.edwards.com/ch-en/aboutus/news-releases/',
        'https://dev.edwards.com/ch-en/aboutus/credo/',
        'https://dev.edwards.com/ch-en/aboutus/ourhistory/',
        'https://dev.edwards.com/ch-en/aboutus/ourleaders/',
        'https://dev.edwards.com/ch-en/aboutus/philanthropy/',
        'https://dev.edwards.com/ch-en/aboutus/what-we-do/',
        'https://dev.edwards.com/ch-en/aboutus/who-we-are/',
        'https://dev.edwards.com/ch-en/aboutus/home/',
        'https://dev.edwards.com/ch-en/careers/',
        'https://dev.edwards.com/ch-en/careers/benefits/',
        'https://dev.edwards.com/ch-en/careers/home/',
        'https://dev.edwards.com/ch-en/careers/diversity-inclusion/',
        'https://dev.edwards.com/ch-en/careers/locations/',
        'https://dev.edwards.com/ch-en/careers/meet-our-employees/',
        'https://dev.edwards.com/ch-en/careers/our-culture/',
        'https://dev.edwards.com/ch-en/careers/professionalareas/',
        'https://dev.edwards.com/ch-en/careers/workinghere/',
        'https://dev.edwards.com/ch-en/',
        'https://dev.edwards.com/ch-en/legal/',
        'https://dev.edwards.com/ch-en/legal/cookie-statement/',
        'https://dev.edwards.com/ch-en/legal/correct-change-personal-information/',
        'https://dev.edwards.com/ch-en/legal/legalterms/',
        'https://dev.edwards.com/ch-en/legal/privacypolicy/',
        'https://dev.edwards.com/ch-en/legal/questions-concerns-about-personal-information/',
        'https://dev.edwards.com/ch-en/legal/remove-info-under-age-13/',
        'https://dev.edwards.com/ch-en/legal/remove-personal-information/',
        'https://dev.edwards.com/ch-en/legal/unsubscribe-remove-from-mailing-lists/',
        'https://dev.edwards.com/ch-en/patients/',
        'https://dev.edwards.com/ch-en/patients/faq/',
        'https://dev.edwards.com/ch-en/patients/glossary/',
        'https://dev.edwards.com/ch-en/patients/patient-events-and-opportunities-interest-form/',
        'https://dev.edwards.com/ch-en/patients/patient-information/',
        'https://dev.edwards.com/ch-en/patients/patient-voice/',
        'https://dev.edwards.com/ch-en/patients/patient-voice-form/',
        'https://dev.edwards.com/ch-en/site-map/'
        }

    if 'e' in params and params['e']=='cr':
        links = {
        'https://dev.edwards.com/cr/404-page-test/',
        'https://dev.edwards.com/cr/aboutus/',
        'https://dev.edwards.com/cr/aboutus/accesshealthcare/',
        'https://dev.edwards.com/cr/aboutus/pastgrant/',
        'https://dev.edwards.com/cr/aboutus/heartbeat/',
        'https://dev.edwards.com/cr/aboutus/news-releases/',
        'https://dev.edwards.com/cr/aboutus/contactusgeneral/',
        'https://dev.edwards.com/cr/aboutus/ehm-guidelines-and-reporting-obligations/',
        'https://dev.edwards.com/cr/aboutus/corporategiving/',
        'https://dev.edwards.com/cr/aboutus/philanthropy/',
        'https://dev.edwards.com/cr/aboutus/ourhistory/',
        'https://dev.edwards.com/cr/aboutus/credo/',
        'https://dev.edwards.com/cr/aboutus/ourleaders/',
        'https://dev.edwards.com/cr/aboutus/global-giving-objectives/',
        'https://dev.edwards.com/cr/aboutus/what-we-do/',
        'https://dev.edwards.com/cr/aboutus/home/',
        'https://dev.edwards.com/cr/aboutus/corp-responsibility/',
        'https://dev.edwards.com/cr/aboutus/global-locations/',
        'https://dev.edwards.com/cr/aboutus/employeevolunteer/',
        'https://dev.edwards.com/cr/careers/',
        'https://dev.edwards.com/cr/careers/professionalareas/',
        'https://dev.edwards.com/cr/careers/benefits/',
        'https://dev.edwards.com/cr/careers/home/',
        'https://dev.edwards.com/cr/careers/meet-our-employees/',
        'https://dev.edwards.com/cr/careers/diversity-inclusion/',
        'https://dev.edwards.com/cr/careers/our-culture/',
        'https://dev.edwards.com/cr/careers/locations/',
        'https://dev.edwards.com/cr/careers/workinghere/',
        'https://dev.edwards.com/cr/',
        'https://dev.edwards.com/cr/legal/',
        'https://dev.edwards.com/cr/legal/remove-info-under-age-13/',
        'https://dev.edwards.com/cr/legal/privacypolicy/',
        'https://dev.edwards.com/cr/legal/legalterms/',
        'https://dev.edwards.com/cr/site-map/',
        'https://dev.edwards.com/cr/patients/',
        'https://dev.edwards.com/cr/patients/glossary/',
        'https://dev.edwards.com/cr/patients/patient-information/',
        'https://dev.edwards.com/cr/patients/faq/',
        'https://dev.edwards.com/cr/patients/implantpatientregistry/',
        'https://dev.edwards.com/cr/patients/patient-voice/',
        'https://dev.edwards.com/cr/cartago/'
        }

    create_workers()
    create_jobs()
    print("---URL scraping time %s seconds for gb urls with /sites/ ---" % (time.time() - start_time))

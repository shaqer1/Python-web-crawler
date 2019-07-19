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
from requests_html import HTMLSession
from Crawler.Form import Form
from Crawler.Tag import Tag
from Crawler.Image import Image
from Crawler.Link import Link
from Crawler.Page import Page
from Crawler.Table import Table
from Image import Save
from Image.Download import Download


usage = 'usage: TODO'

if __name__ == '__main__':
    params = {}

    # if len(sys.argv)%2!=1: #TODO add extension for start and baseurl,
    #     print('wrong number of args', usage)
    #     quit()

    for i in range(len(sys.argv)):
        if('-'==sys.argv[i][0]):
            if sys.argv[i][1:len(sys.argv)] == 'tag':
                params[sys.argv[i][1:len(sys.argv)]] = [sys.argv[i+1],sys.argv[i+2],sys.argv[i+3]]
            else:
                params[sys.argv[i][1:len(sys.argv)]]=sys.argv[i+1]
            

    # print(params)
    URL = params['u']
    NUMBER_OF_THREADS = 4
    if 'threads' in params:
        NUMBER_OF_THREADS = int(params['threads'])
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
                    linksFound = filterURL(page.fetch_links(""), URL)
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
        # print('\n\nPrinting array')
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
                    img = Image(link) #TODO add a param for html
                    if(link in visited):
                        html = visited[link]
                    images = img.fetch_links(html)
                    visited[link] = img.html_string
                    images = filterNonImages(images, params['i'])

                
                if 'l' in params:
                    linkOBJ = Link(link)
                    if(link in visited):
                        html = visited[link]
                    linksOBJ = linkOBJ.fetch_links(html)
                    visited[link] = linkOBJ.html_string
                    linksOBJ = filterNonLinks(linksOBJ, params['l'])

                if 't' in params:
                    table = Table(link) #TODO add a param for html
                    if(link in visited):
                        html = visited[link]
                    tables = table.fetch_links(html)
                    visited[link] = table.html_string

                if 'f' in params:
                    form = Form(link) #TODO add a param for html
                    if(link in visited):
                        html = visited[link]
                    forms = filterForms(form.fetch_links(html), params['f']) # mktoForm
                    visited[link] = form.html_string

                if 'tag' in params:
                    tag = Tag(URL, link, params['tag'][0], params['tag'][1])
                    if(link in visited):
                        html = visited[link]
                    if 'child' in params:
                        tagMap = parseArgs(params['child'])
                        tag.addTagMap(tagMap)
                        tag.addTagMapQuery(params['tag'][2])
                    tags = tag.fetch_links(html)

                with lock:
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
            linksFound = filterURL(page.fetch_links(""), URL)
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
        'https://dev.edwards.com/gb/aboutus/',
        'https://dev.edwards.com/gb/aboutus/clinical-education-support/',
        'https://dev.edwards.com/gb/aboutus/contactus/',
        'https://dev.edwards.com/gb/aboutus/contactusgeneral/',
        'https://dev.edwards.com/gb/aboutus/contactusimage/',
        'https://dev.edwards.com/gb/aboutus/contactusproduct/',
        'https://dev.edwards.com/gb/aboutus/corp-responsibility/',
        'https://dev.edwards.com/gb/aboutus/edi/',
        'https://dev.edwards.com/gb/aboutus/employeevolunteer/',
        'https://dev.edwards.com/gb/aboutus/europe-ems-policy/',
        'https://dev.edwards.com/gb/aboutus/events/',
        'https://dev.edwards.com/gb/aboutus/every-heartbeat-matters/',
        'https://dev.edwards.com/gb/aboutus/heartbeat/',
        'https://dev.edwards.com/gb/aboutus/ehm-guidelines-and-reporting-obligations/',
        'https://dev.edwards.com/gb/aboutus/corporategiving/',
        'https://dev.edwards.com/gb/aboutus/global-giving-objectives/',
        'https://dev.edwards.com/gb/aboutus/pastgrant/',
        'https://dev.edwards.com/gb/aboutus/accesshealthcare/',
        'https://dev.edwards.com/gb/aboutus/global-locations/',
        'https://dev.edwards.com/gb/aboutus/news-releases/',
        'https://dev.edwards.com/gb/aboutus/credo/',
        'https://dev.edwards.com/gb/aboutus/ourhistory/',
        'https://dev.edwards.com/gb/aboutus/ourleaders/',
        'https://dev.edwards.com/gb/aboutus/patient-stories/',
        'https://dev.edwards.com/gb/aboutus/philanthropy/',
        'https://dev.edwards.com/gb/aboutus/physicians-finance/',
        'https://dev.edwards.com/gb/aboutus/political-disclosure/',
        'https://dev.edwards.com/gb/aboutus/reimbursement/',
        'https://dev.edwards.com/gb/aboutus/romanian-financial-relationships/',
        'https://dev.edwards.com/gb/aboutus/what-we-do/',
        'https://dev.edwards.com/gb/aboutus/home/',
        'https://dev.edwards.com/gb/advanced-hemodynamic-monitoring/',
        'https://dev.edwards.com/gb/andy-test-page/',
        'https://dev.edwards.com/gb/careers/',
        'https://dev.edwards.com/gb/careers/benefits/',
        'https://dev.edwards.com/gb/careers/home/',
        'https://dev.edwards.com/gb/careers/development-programs/',
        'https://dev.edwards.com/gb/careers/diversity-inclusion/',
        'https://dev.edwards.com/gb/careers/finance-development-program/',
        'https://dev.edwards.com/gb/careers/internships/',
        'https://dev.edwards.com/gb/careers/locations/',
        'https://dev.edwards.com/gb/careers/meet-our-employees/',
        'https://dev.edwards.com/gb/careers/our-culture/',
        'https://dev.edwards.com/gb/careers/professionalareas/',
        'https://dev.edwards.com/gb/careers/professional-development/',
        'https://dev.edwards.com/gb/careers/recruitingcalender/',
        'https://dev.edwards.com/gb/careers/tdp/',
        'https://dev.edwards.com/gb/careers/universityengineeringprogram/',
        'https://dev.edwards.com/gb/careers/universitysummerprogram/',
        'https://dev.edwards.com/gb/careers/workinghere/',
        'https://dev.edwards.com/gb/cceducationform/',
        'https://dev.edwards.com/gb/devices/',
        'https://dev.edwards.com/gb/devices/accessories/',
        'https://dev.edwards.com/gb/devices/accessories/atraumatic-occlusion/',
        'https://dev.edwards.com/gb/devices/accessories/vascushunt-ii-silicone-carotid-shunt/',
        'https://dev.edwards.com/gb/devices/annuloplasty/',
        'https://dev.edwards.com/gb/devices/annuloplasty/mitral-heart-valve-repair/',
        'https://dev.edwards.com/gb/devices/annuloplasty/tricuspid-heart-valve-repair/',
        'https://dev.edwards.com/gb/devices/catheters/',
        'https://dev.edwards.com/gb/devices/catheters/arterial-cannulae/',
        'https://dev.edwards.com/gb/devices/catheters/clot-management/',
        'https://dev.edwards.com/gb/devices/catheters/occlusion/',
        'https://dev.edwards.com/gb/devices/catheters/general-surgery/',
        'https://dev.edwards.com/gb/devices/catheters/vascular/',
        'https://dev.edwards.com/gb/devices/central-venous-access/',
        'https://dev.edwards.com/gb/devices/central-venous-access/ava-3xi/',
        'https://dev.edwards.com/gb/devices/central-venous-access/ava-high-flow/',
        'https://dev.edwards.com/gb/devices/decision-software/',
        'https://dev.edwards.com/gb/devices/decision-software/hpi/',
        'https://dev.edwards.com/gb/devices/heart-valves/',
        'https://dev.edwards.com/gb/devices/heart-valves/aortic-pericardial/',
        'https://dev.edwards.com/gb/devices/heart-valves/centera/',
        'https://dev.edwards.com/gb/devices/heart-valves/intuity/',
        'https://dev.edwards.com/gb/devices/heart-valves/mitral/',
        'https://dev.edwards.com/gb/devices/heart-valves/resilia/',
        'https://dev.edwards.com/gb/devices/heart-valves/sapien-xt-valve/',
        'https://dev.edwards.com/gb/devices/heart-valves/aortic/',
        'https://dev.edwards.com/gb/devices/heart-valves/surgical-valve-technologies/',
        'https://dev.edwards.com/gb/devices/heart-valves/transcatheter/',
        'https://dev.edwards.com/gb/devices/heart-valves/transcatheter-sapien-xt-valve-pulmonic/',
        'https://dev.edwards.com/gb/devices/heart-valves/transcatheter-sapien-3-ultra/',
        'https://dev.edwards.com/gb/devices/heart-valves/transcatheter-sapien-3/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/acumen-analytics/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/clearsight/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/ev1000/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/flotrac/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/hemosphere/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/monitoring-platforms/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/oximetry-central-venous-catheter/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/pediasat-catheter/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/swan-ganz-catheters/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/tissue-oximetry/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/tissue-oximetry/thankyou/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/vigileo-monitor/',
        'https://dev.edwards.com/gb/devices/hemodynamic-monitoring/volumeview/',
        'https://dev.edwards.com/gb/devices/home/',
        'https://dev.edwards.com/gb/devices/minimal-incision-mvr-avr/',
        'https://dev.edwards.com/gb/devices/pressure-monitoring/',
        'https://dev.edwards.com/gb/devices/pressure-monitoring/closed-blood-sampling/',
        'https://dev.edwards.com/gb/devices/pressure-monitoring/transducer/',
        'https://dev.edwards.com/gb/devices/pressure-monitoring/truclip-holder/',
        'https://dev.edwards.com/gb/devices/transcatheter-valve-repair/',
        'https://dev.edwards.com/gb/devices/transcatheter-valve-repair/cardiobandmitralsystem/',
        'https://dev.edwards.com/gb/devices/transcatheter-valve-repair/cardiobandtricuspidsystem/',
        'https://dev.edwards.com/gb/devices/transcatheter-valve-repair/pascal/',
        'https://dev.edwards.com/gb/download-pgdt-analytics/',
        'https://dev.edwards.com/gb/education/',
        'https://dev.edwards.com/gb/clinicaleducation/',
        'https://dev.edwards.com/gb/welcome-to-edwards-lifesciences/',
        'https://dev.edwards.com/gb/edwards-lunch-symposium-the-esicm-lives-congress-2015/',
        'https://dev.edwards.com/gb/ehm-guidelines-and-reporting-obligations/',
        'https://dev.edwards.com/gb/esicm2016/',
        'https://dev.edwards.com/gb/etpage/',
        'https://dev.edwards.com/gb/forms/',
        'https://dev.edwards.com/gb/forms/productcategorypicker/',
        'https://dev.edwards.com/gb/forms/request-a-copy-of-sepsis-bundle-guidelines-overview/',
        'https://dev.edwards.com/gb/harpoon-beating-heart-mitral-valve-system/',
        'https://dev.edwards.com/gb/',
        'https://dev.edwards.com/gb/investors/',
        'https://dev.edwards.com/gb/legal/',
        'https://dev.edwards.com/gb/legal/cookie-statement/',
        'https://dev.edwards.com/gb/legal/correct-change-personal-information-copy/',
        'https://dev.edwards.com/gb/legal/correct-change-personal-information/',
        'https://dev.edwards.com/gb/legal/legalterms/',
        'https://dev.edwards.com/gb/legal/privacypolicy/',
        'https://dev.edwards.com/gb/legal/questions-concerns-about-personal-information/',
        'https://dev.edwards.com/gb/legal/remove-info-under-age-13/',
        'https://dev.edwards.com/gb/legal/remove-personal-information/',
        'https://dev.edwards.com/gb/new-releases/',
        'https://dev.edwards.com/gb/patients/',
        'https://dev.edwards.com/gb/patients/faq/',
        'https://dev.edwards.com/gb/patients/glossary/',
        'https://dev.edwards.com/gb/patients/patient-events-and-opportunities-interest-form/',
        'https://dev.edwards.com/gb/patients/patient-information/',
        'https://dev.edwards.com/gb/patients/patient-voice/',
        'https://dev.edwards.com/gb/patients/patient-voice-form/',
        'https://dev.edwards.com/gb/procedures/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/evaluation/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/guidelines/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/awareness/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/options/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/partner/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/prevalence/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/progression/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/referral/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/results/',
        'https://dev.edwards.com/gb/procedures/aorticstenosis/standard/',
        'https://dev.edwards.com/gb/products/',
        'https://dev.edwards.com/gb/site-map/',
        'https://dev.edwards.com/gb/specialty-teams/',
        'https://dev.edwards.com/gb/specialty-teams/heart-team/',
        'https://dev.edwards.com/gb/specialty-teams/icu-solutions/',
        'https://dev.edwards.com/gb/test/',
        'https://dev.edwards.com/gb/therapies/',
        'https://dev.edwards.com/gb/therapies/blood-management/',
        'https://dev.edwards.com/gb/therapies/fluid-management/',
        'https://dev.edwards.com/gb/therapies/hypotension-management/',
        'https://dev.edwards.com/gb/therapies/or-solutions-for-esr/',
        'https://dev.edwards.com/gb/therapies/registernow/',
        'https://dev.edwards.com/gb/trialsolutions/',
        'https://dev.edwards.com/gb/try/',
        'https://dev.edwards.com/gb/unsubscribe-remove-from-mailing-lists/',
        'https://dev.edwards.com/gb/xt-reimbursement/',
        'https://dev.edwards.com/gb/xvrdms-8179/',
        'https://dev.edwards.com/gb/xvrtestpage/'
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
        'https://dev.edwards.com/ch-en/site-map/',
        'https://dev.edwards.com/ch-en/xvrdms-8179/'
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

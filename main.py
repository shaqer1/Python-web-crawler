import os.path
import sys
import threading
import time
from queue import Queue
from Models.Complete.Image import Image
from Models.Complete.Link import Link
from Models.Complete.Table import Table

import functions
from Crawler.Image import Image
from Crawler.Link import Link
from Crawler.Page import Page
from Crawler.Table import Table
from Image import Save
from Image.Download import Download

URL = sys.argv[1]

if __name__ == '__main__':
    NUMBER_OF_THREADS = 4
    queue = Queue()


    page = Page(URL+ '/site-map')

    
    


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

                img = Image(link) #TODO add a param for html
                if(link in visited):
                    html = visited[link]
                images = img.fetch_links(html)
                visited[link] = img.html_string
                images = filterNonImages(images, '/sites/4/')

                
                linkOBJ = Link(link)
                if(link in visited):
                    html = visited[link]
                linksOBJ = linkOBJ.fetch_links(html)
                visited[link] = linkOBJ.html_string
                linksOBJ = filterNonLinks(linksOBJ, '/gb/')


                # table = Table(link) #TODO add a param for html
                # if(link in visited):
                    # html = visited[link]
                # tables = table.fetch_links(html)
                # visited[link] = table.html_string

                if(len(linksOBJ)>0 or len(images)>0):
                    print(threading.current_thread().name + ' fetched URL:' + link)

                if(len(linksOBJ)>0):
                    print('------Links-----')
                    printJSON(linksOBJ)

                if(len(images)>0):
                    print('\n\n------Images-----')
                    printJSON(images)

                if(len(linksOBJ)>0 or len(images)>0):
                    print('END\n\n')

                # down = Download(links=images, path=functions.get_folder_name(link))
                # down.start()

                # print('\n\n------Tables class-----')
                # if(len(tables)> 0):
                #     printJSON(tables)


                queue.task_done()
                if queue.empty():
                    break
            except:
                queue.task_done()
                continue

    def scrapeLinks(page, URL, links, visited):
        if page.page_url not in visited:
            l1 = len(links)
            linksFound = filterURL(page.fetch_links(), URL)
            links = links.union(linksFound)
            visited[page.page_url] = page.html_string
            if l1 == len(links):
                return links
            print('found', len(links), 'visited', len(visited))
            for link in links:
                links = scrapeLinks(Page(link), URL, links, visited)
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
        
    links = set()
    visited = {}
    # start_time = time.time()
    # links = scrapeLinks(page, URL, links, visited)
    # printJSON(links)
    # print("---URL scraping time %s seconds ---" % (time.time() - start_time))


    start_time = time.time()
    #GB
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
    # links = {
    # 'https://dev.edwards.com/ch-en/aboutus/',
    # 'https://dev.edwards.com/ch-en/aboutus/contactusgeneral/',
    # 'https://dev.edwards.com/ch-en/aboutus/corp-responsibility/',
    # 'https://dev.edwards.com/ch-en/aboutus/employeevolunteer/',
    # 'https://dev.edwards.com/ch-en/aboutus/europe-ems-policy/',
    # 'https://dev.edwards.com/ch-en/aboutus/heartbeat/',
    # 'https://dev.edwards.com/ch-en/aboutus/ehm-guidelines-and-reporting-obligations/',
    # 'https://dev.edwards.com/ch-en/aboutus/corporategiving/',
    # 'https://dev.edwards.com/ch-en/aboutus/global-giving-objectives/',
    # 'https://dev.edwards.com/ch-en/aboutus/pastgrant/',
    # 'https://dev.edwards.com/ch-en/aboutus/accesshealthcare/',
    # 'https://dev.edwards.com/ch-en/aboutus/global-locations/',
    # 'https://dev.edwards.com/ch-en/aboutus/news-releases/',
    # 'https://dev.edwards.com/ch-en/aboutus/credo/',
    # 'https://dev.edwards.com/ch-en/aboutus/ourhistory/',
    # 'https://dev.edwards.com/ch-en/aboutus/ourleaders/',
    # 'https://dev.edwards.com/ch-en/aboutus/philanthropy/',
    # 'https://dev.edwards.com/ch-en/aboutus/what-we-do/',
    # 'https://dev.edwards.com/ch-en/aboutus/who-we-are/',
    # 'https://dev.edwards.com/ch-en/aboutus/home/',
    # 'https://dev.edwards.com/ch-en/careers/',
    # 'https://dev.edwards.com/ch-en/careers/benefits/',
    # 'https://dev.edwards.com/ch-en/careers/home/',
    # 'https://dev.edwards.com/ch-en/careers/diversity-inclusion/',
    # 'https://dev.edwards.com/ch-en/careers/locations/',
    # 'https://dev.edwards.com/ch-en/careers/meet-our-employees/',
    # 'https://dev.edwards.com/ch-en/careers/our-culture/',
    # 'https://dev.edwards.com/ch-en/careers/professionalareas/',
    # 'https://dev.edwards.com/ch-en/careers/workinghere/',
    # 'https://dev.edwards.com/ch-en/',
    # 'https://dev.edwards.com/ch-en/legal/',
    # 'https://dev.edwards.com/ch-en/legal/cookie-statement/',
    # 'https://dev.edwards.com/ch-en/legal/correct-change-personal-information/',
    # 'https://dev.edwards.com/ch-en/legal/legalterms/',
    # 'https://dev.edwards.com/ch-en/legal/privacypolicy/',
    # 'https://dev.edwards.com/ch-en/legal/questions-concerns-about-personal-information/',
    # 'https://dev.edwards.com/ch-en/legal/remove-info-under-age-13/',
    # 'https://dev.edwards.com/ch-en/legal/remove-personal-information/',
    # 'https://dev.edwards.com/ch-en/legal/unsubscribe-remove-from-mailing-lists/',
    # 'https://dev.edwards.com/ch-en/patients/',
    # 'https://dev.edwards.com/ch-en/patients/faq/',
    # 'https://dev.edwards.com/ch-en/patients/glossary/',
    # 'https://dev.edwards.com/ch-en/patients/patient-events-and-opportunities-interest-form/',
    # 'https://dev.edwards.com/ch-en/patients/patient-information/',
    # 'https://dev.edwards.com/ch-en/patients/patient-voice/',
    # 'https://dev.edwards.com/ch-en/patients/patient-voice-form/',
    # 'https://dev.edwards.com/ch-en/site-map/',
    # 'https://dev.edwards.com/ch-en/xvrdms-8179/'
    # }

    #links = {
    #'https://dev.edwards.com/cr/aboutus/',
    #'https://dev.edwards.com/cr/aboutus/accesshealthcare/',
    #'https://dev.edwards.com/cr/aboutus/pastgrant/',
    #'https://dev.edwards.com/cr/aboutus/heartbeat/',
    #'https://dev.edwards.com/cr/aboutus/news-releases/',
    #'https://dev.edwards.com/cr/aboutus/contactusgeneral/',
    #'https://dev.edwards.com/cr/aboutus/ehm-guidelines-and-reporting-obligations/',
    #'https://dev.edwards.com/cr/aboutus/corporategiving/',
    #'https://dev.edwards.com/cr/aboutus/philanthropy/',
    #'https://dev.edwards.com/cr/aboutus/ourhistory/',
    #'https://dev.edwards.com/cr/aboutus/credo/',
    #'https://dev.edwards.com/cr/aboutus/ourleaders/',
    #'https://dev.edwards.com/cr/aboutus/global-giving-objectives/',
    #'https://dev.edwards.com/cr/aboutus/what-we-do/',
    #'https://dev.edwards.com/cr/aboutus/home/',
    #'https://dev.edwards.com/cr/aboutus/corp-responsibility/',
    #'https://dev.edwards.com/cr/aboutus/global-locations/',
    #'https://dev.edwards.com/cr/aboutus/employeevolunteer/',
    #'https://dev.edwards.com/cr/careers/',
    #'https://dev.edwards.com/cr/careers/professionalareas/',
    #'https://dev.edwards.com/cr/careers/benefits/',
    #'https://dev.edwards.com/cr/careers/home/',
    #'https://dev.edwards.com/cr/careers/meet-our-employees/',
    #'https://dev.edwards.com/cr/careers/diversity-inclusion/',
    #'https://dev.edwards.com/cr/careers/our-culture/',
    #'https://dev.edwards.com/cr/careers/locations/',
    #'https://dev.edwards.com/cr/careers/workinghere/',
    #'https://dev.edwards.com/cr/',
    #'https://dev.edwards.com/cr/legal/',
    #'https://dev.edwards.com/cr/legal/remove-info-under-age-13/',
    #'https://dev.edwards.com/cr/legal/privacypolicy/',
    #'https://dev.edwards.com/cr/legal/legalterms/',
    #'https://dev.edwards.com/cr/site-map/',
    #'https://dev.edwards.com/cr/patients/',
    #'https://dev.edwards.com/cr/patients/glossary/',
    #'https://dev.edwards.com/cr/patients/patient-information/',
    #'https://dev.edwards.com/cr/patients/faq/',
    #'https://dev.edwards.com/cr/patients/implantpatientregistry/',
    #'https://dev.edwards.com/cr/patients/patient-voice/',
    #'https://dev.edwards.com/cr/cartago/'
    #}

    create_workers()
    create_jobs()
    print("---URL scraping time %s seconds for gb urls with /sites/ ---" % (time.time() - start_time))

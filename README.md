# Multi threading image crawler in python 3
Find all the images/links/table classes from a domain and download to your project folder. More tags and links to fetch can be added as well

## Features
- Multithreaded
- Preserves data fetched in every run for faster results
- fetches URLS on domain recursively/through threads
- Basic Auth for pages

## Requirements

- Python3

## Usage

```bash
python3 ./main.py -u 'https://domain.com/extension' -e 'extension' -l '<delimitor>' -i '<delimitor>' -threads '<num threads>' -ext '<extension to start with>' -layers '<#of layers to crawl>' -d '<Download file limit>' -auth[A] auth_default.json
```

## Parameters
### Base URL: 
#### `-u <Param1>`
    - This param takes a base_url <Param 1> this is where the crawling begins.
    - This param is ***required***
## Specify Links (pick only one of the following params)

### Fixed links to crawl: 
#### `-e <Param1>`
    - This param takes a file name <Param 1>, that is in JSON format with an array called links, with fixed links to crawl for tags and images etc.
    - use this param instead of the threads and ext tag
### Thread crawling:
#### `-threads <Param1>`
    - Crawls base url recursively by using threads and extract all sub links, hence creating a tree of links on site
    - Param1 specifies number of threads to use
    - This cannot be used with -e or -layers
    - if threads tag is not present then it recursively fetches links in main thread

## Extra options

### Extension for crawling:
#### `-ext <Param1>`
    - extracts all links by using threads or recursively, but starts at `URL=(base_url+<Param1>)`
    - example `-ext /sitemap`
### Number of layers to crawl:
#### `-layers <Param1>`
    - when fetching links recursively or with links then only <Param1> layers deep are crawled
### Export results to CSV file:
#### `-csv <Param1>`
    - exports results in csv format given by: pageUrl,listItem1,listItem2,listItem3,...listItemLast\n
    - exported to file <param1>
### filter list of results:
#### `-filterBase <Param1>`
    - <Param1> param is taken out of results, if you only need the endpoints not the complete URL

## Extraction params

### Extract Links: 
#### ` -l <Param1>`
    - This param is used to specify that the *anchor* tag's *href* atribute will be fetched.
    - the required param is used to filter links that don't have <Param1> in them
### Extract Images: 
#### ` -i <Param1>`
    - This param is used to specify that the *img* tag's *src* atribute will be fetched.
    - the required param is used to filter links that don't have <Param1> in them
#####   `-d <Param1>`
`#TODO currently this feature is in development`

            - downloads Param1 number of images crawled, if no parameter specified it downloads all
### Extract Table classes:
#### `-t `
    - fetches table tag and extracts class attribute.
### Extract Forms:
#### `-f <Param1>`
    - This param is used to specify that the *form* tag's *class* atribute will be fetched.
    - the required param is used to filter links that have <Param1> in them
### Extract other elements:
#### `-tag <Param1> <Param2> <Param3>`
    - Used to fetch <Param1> tags on page and extract <Param2> attribute
    - <Param3> is used if -child is specified
    - example: `-tag div class` extract class of all divs
#####   `-child "tag1":"attr1"-"tag2":"attr2"`
            - used with -tag only
            - Used to fetch <Param1> tags on page and extract <Param2> attribute, filtered by <Param3> 
            - `"tag1":"attr1"-"tag2":"attr2"` represents a variable list of tag and attribute pairs to extract
            - Fetches tag attribute pairs that are descendants of the tags specified by -tag param
            - example: `-tag div class page-banner -child "img":"src"-"source":"src-set"` extract all img tag's src and source tag's src-set that have div as parent with class == page-banner

## Authentication

### Autheticate when needed:
#### `-auth auth.json keyToken`
    - authenticates when fetching page, auth params are provided in auth.json, a template auth_default.json is in workspace folder.
    - keyToken is secret token provided in html of page or in request when performing browser sign in.
    - keyToken can be extracted from page by inspecting page or network requests on page.
    - this key needs to be changed in auth.json as well, NOTE: this is no the token refreshed everytime, just the input key to extract everytime
    - detailed explaination of auth.json below
### Autheticate all the time:
#### `-authA auth.json keyToken`
    - authenticates everytime with same configuration as -auth

## Auth.json

1. Replace `usernameNameField` with name attribute of the login's username input name attribute
2. Replace `password` with name attribute of the login's passwrod input name attribute
3.  Replace `hiddenTokenName` with name attribute of the login's passwrod input name attribute
4.  Replace `loginPostURL` value with URl that request is sent to in chrome debugger
5.  Replace `authURL` value with URl to get so that it redirects to login page, this will be used to get the login keyToken
##### Optional
5.  Replace `logOffUrl` value with URl that logsOff user so that this URL isn't accidentally crawled
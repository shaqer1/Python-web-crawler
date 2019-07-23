# Multi threading image crawler in python 3
Find all the images/links/table classes from a domain and download to your project folder. More tags and links to fetch can be added as well

## Features
- Multithreaded
- Preserves data fetched in every run for faster results
- fetches URLS on domain recursively/through threads

### Requirements

- Python3

### Usage

```bash
python3 ./main.py -u 'https://domain.com/extension' -e 'extension' -l '<delimitor>' -i '<delimitor>' -threads '<num threads>' -ext '<extension to start with>' -layers '<#of layers to crawl>' -d '<Download file limit>'
```

### Options

```bash
-e: Endpoint to fetch links (if applicable) If not provided it recursively fetches urls to crawl #TODO remove
-u: Base URL
-l: Fetch links which don't have the following delimitor
-t: Fetch tables classes 
-f: fetch form tag with class of Param
-tag: params: <tag> <attr> <filter>, fetches tag with attribute filtered by <filter> 
-child: params: "tag1":"attr1"-"tag2":"attr2" used with -tag to fetch specific tag's attribute value
-i: Fetch images which don't have the following delimitor
-threads: whether to use threads and how many
-ext: extension on domain to start with appended to base in beginning
-layers: how deep to crawl in layers, if not specified then infinite
-d: download file limit, leave at 0 #TODO
-csv: export results to csv filename=PARAM, format, is link, tag
-filterBase: filterBase param is taken out of results, if you only need the endpoints
```

# Multi threading image crawler in python 3
Find all the images/links/table classes from a website and download to your project folder. More tags and links to fetch can be added as well

## Features
- Multithreaded
- Preserves data fetched in every run for faster results
- fetches URLS on domain recursively/through threads

### Requirements

- Python3

### Usage

```bash
python3 ./main.py -u 'https://domain.com/extension' -e 'extension' -l '<delimitor>' -i '<delimitor>'
```

### Options

```bash
-e: Endpoint to fetch links (if applicable) If not provided it recursively fetches urls to crawl
-u: Base URL
-l: Fetch links which don't have the following delimitor
-i: Fetch images which don't have the following delimitor
```

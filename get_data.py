import os, re, sys
from BeautifulSoup import BeautifulSoup
from glob import glob
from json import loads
from mechanize import Browser

from iterview import iterview
from utilities import download_url, makedir, safe_write

DATA_DIR = 'data'

CACHE = os.path.join(DATA_DIR, 'cache')

LISTING_URLS_FILE = os.path.join(CACHE, 'listing_urls.txt')

HTML_DIR = os.path.join(CACHE, 'html')
SEARCH_RESULTS_DIR = os.path.join(HTML_DIR, 'search_results')
LISTING_PAGES_DIR = os.path.join(HTML_DIR, 'listing_pages')

CSV_FILE = os.path.join(DATA_DIR, 'data.csv')

SEARCH_URL = 'http://streeteasy.com/rentals'


def get_listing_urls(br):
    """
    Searches StreetEasy for all rental apartment listings in
    Williamsburg, caches each page of search results to the directory
    whose name is stored in the variable SEARCH_RESULTS_DIR, and
    caches the URLs for the listings (one per line) to the file whose
    name is stored in the variable LISTING_URLS_FILE.

    Arguments:

    br -- Browser object
    """

    if os.path.exists(LISTING_URLS_FILE):
        return

    makedir(os.path.dirname(LISTING_URLS_FILE))

    br.open(SEARCH_URL)

    br.select_form(nr=1)
#    print br.form
    br.form['area[]'] = ['302']
    response = br.submit()
    results_url = response.geturl()

    with safe_write(LISTING_URLS_FILE) as f:
        while True:

            filename = download_url(br, results_url, SEARCH_RESULTS_DIR)
            soup = BeautifulSoup(file(filename).read())

            results = soup.findAll('div', attrs={'class': 'details_title' })

            urls = []

            for r in results:

                r = r.find('h5')
                r = r.find('a')
                r = r.get('href')

                urls.append('http://streeteasy.com' + r)

#            urls = ['http://www.streeteasy.com' + r.find('h5').find('a').get('href') for r in soup.findAll('div', attrs={'class': 'details_title' })]

            f.write('\n'.join(urls))
            f.write('\n')
            f.flush()

            nav = soup.find('a', attrs={'class': 'next_page'})

            try:
                results_url = 'http://www.streeteasy.com' + nav.get('href')
            except AttributeError:
                break


def get_listing_pages(br):
    """
    Caches the contents of each URL in the file whose name is stored
    in the variable LISTING_URLS_FILE to the directory whose name is
    stored on the variable LISTING_PAGES_DIR. The contents of each URL
    will be stored in a file whose name is that URL's md5 hash.

    Arguments:

    br -- Browser object
    """

    listing_urls = [url.strip() for url in file(LISTING_URLS_FILE)]

    for url in iterview(listing_urls):
        try:
            download_url(br, url, LISTING_PAGES_DIR)
        except Exception as e:
            print >> sys.stderr, '\n', (url, e)


def get_listing_data():

    with safe_write(CSV_FILE) as f:
        for filename in iterview(glob(LISTING_PAGES_DIR + '/*')):

            contents = file(filename).read()
#            print contents

            try:
                [obj] = re.findall('dataLayer\s*=\s*\[(.*)\];', contents)
                obj = loads(obj)
            except ValueError:
                return

            if 'listPrice' in obj and 'listBed' in obj:
                text = '\t'.join((os.path.basename(filename),
                                  str(obj['listPrice']), str(obj['listBed'])))
                f.write(text)
                f.write('\n')
                f.flush()


def main():

    br = Browser()
    br.set_handle_robots(False) # ignore robots.txt

    get_listing_urls(br)
    get_listing_pages(br)
    get_listing_data()


if __name__ == '__main__':

    main()

    from numpy import loadtxt
    from pylab import plot, show, xlim

    data = loadtxt('data/data.csv', usecols=[1, 2])
    plot(data[:, 0], data[:, 1], 'x')
#    xlim(0, 8000)
    show()

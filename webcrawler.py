
import sys
import numpy as np

from urllib.parse import urlparse
from pathlib import Path
import os
import shutil
import tldextract
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup, SoupStrainer


# number of unique urls to download
TARGET_URLS = 100

# temporary directory to store html files
HTML_DIR = "htmls"


class SimpleWebCrawler:
    def __init__(self, url):
        self.start_url = url

        self.url_array = np.empty(shape=TARGET_URLS, dtype=object)
        self.urls_found = 0
        self.urls_searched = 0

        self.html_dir = Path(HTML_DIR).absolute()
        if os.path.exists(self.html_dir):
            shutil.rmtree(self.html_dir)  # clear existing directory
        os.mkdir(self.html_dir)  # create fresh directory

        # selenium
        driver_options = Options()
        driver_options.headless = True
        self.driver = webdriver.Firefox(options=driver_options)
        self.driver.set_page_load_timeout(20)  # in seconds

    def search(self):
        # start search from start_url
        self.search_url(self.start_url, inc_searched=False)

    def search_url(self, url_to_search, inc_searched=True):
        link_soup = self.get_html_link_soup(url_to_search)

        if link_soup is None:
            print("Stopped search")
            return

        # find all links in the soup
        self.find_urls(link_soup)

        if self.urls_found == TARGET_URLS:
            # stop search
            return

        # update pointer to next found url to search
        if inc_searched:
            self.urls_searched += 1

        if self.urls_found == self.urls_searched:
            print("Ran out of links to search from")
            return

        # search the next url in the list
        self.search_url(self.url_array[self.urls_searched])

    # Returns a file path to store html for given url
    def get_html_fp(self, url):
        filename = f"{tldextract.extract(url).domain}-{self.urls_searched}.html"
        return self.html_dir / filename

    # Downloads html from url to a file
    # Returns negative int if download failed
    def download_html(self, url, html_fp):
        try:
            # open url
            self.driver.get(url)

            # render js
            outer_html = self.driver.execute_script(
                "return document.documentElement.outerHTML;"
            )

            # save html to file
            with open(html_fp, 'w') as fp:
                fp.write(outer_html)
        except TimeoutException:
            print(f"{url} timed out")
            return -1
        except Exception:
            print(f"Unknown error with {url}")
            return -1

        return 0

    # Downloads html from url and returns BeautifulSoup object
    # which is filtered to only contain <a> tags
    def get_html_link_soup(self, url):
        html_fp = self.get_html_fp(url)

        if self.download_html(url, html_fp) < 0:
            # download failed
            return None

        # create bs object
        with open(html_fp, 'r') as fp:
            site_content = fp.read()

        # Only keep <a> tags
        soup = BeautifulSoup(site_content, 'html.parser', parse_only=SoupStrainer("a"))
        return soup

    @staticmethod
    def get_valid_urls(link_soup):
        valid_urls = []
        for link in link_soup:
            if hasattr(link, 'href'):
                try:
                    url = link['href']
                    if is_url(url):
                        valid_urls.append(url)
                except KeyError:
                    # ignore this link
                    continue
        return valid_urls

    # get all unique links and store in url_array
    def find_urls(self, link_soup):
        links = self.get_valid_urls(link_soup)
        link_arr = np.array(links, dtype=object)

        # narrow list to unique links to be added to url_array
        link_arr = np.unique(link_arr)
        # url_array must be unique
        link_arr = np.setdiff1d(link_arr, self.url_array, assume_unique=True)

        links_left = TARGET_URLS - self.urls_found
        links_found = get_np_arrlen(link_arr)
        if links_found <= links_left:
            # all links can fit in url_array
            self.url_array[self.urls_found:self.urls_found + links_found] = link_arr
            self.urls_found += links_found
        else:
            # fill the rest of url_array
            rem_links = link_arr[0:links_left]
            self.url_array[self.urls_found:] = rem_links
            self.urls_found = TARGET_URLS

    def cleanup(self):
        self.driver.quit()


# Returns the length of a single-row array
def get_np_arrlen(arr):
    return arr.shape[0]


# Returns True if cand_str is a properly-formatted url
def is_url(cand_str):
    parse_result = urlparse(cand_str)
    return parse_result.scheme != "" and parse_result.netloc != ""


def main(url):
    # sanity check on input url
    if not is_url(url):
        print("Invalid url given. Please try again with a valid url.")
        sys.exit(-1)

    # run webcrawler
    wc = SimpleWebCrawler(url)
    wc.search()

    # print urls found
    print(f"Found {wc.urls_found} unique URLs:")
    for i, found_url in enumerate(wc.url_array):
        print(f"{i + 1}. {found_url}")

    wc.cleanup()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Incorrect number of arguments. Correct format: python3 webcrawler.py <url>")

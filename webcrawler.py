
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
from bs4 import BeautifulSoup


# number of unique urls to download
TARGET_URLS = 100

HTML_DIR = "htmls"

# testing parameter
DEBUG = True


class SimpleWebCrawler:
    def __init__(self, url):
        self.start_url = url

        self.url_array = np.empty(shape=TARGET_URLS, dtype=str)
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

    @staticmethod
    def is_url(cand_str):
        parse_result = urlparse(cand_str)
        return parse_result.scheme != "" and parse_result.netloc != ""

    def search(self):
        # start search from start_url
        self.search_url(self.start_url, inc_searched=False)

    def search_url(self, url_to_search, inc_searched=True):
        soup = self.get_html_soup(url_to_search)

        if soup is None:
            print("Stopped search")
            return

        # get all hrefs and store in url_array
        # update urls_found accordingly
        # this function should break early if urls_found hits TARGET_URLS

        # check if TARGET_URLS is hit
        if self.urls_found == TARGET_URLS:
            # stop search
            return
        else:
            # update pointer to next url to search
            if inc_searched:
                self.urls_searched += 1

            # search the next url in the list
            self.search_url(self.url_array[self.urls_searched])

    def get_html_fp(self, url):
        filename = f"{tldextract.extract(url).domain}-{self.urls_searched}.html"
        return self.html_dir / filename

    def get_html_soup(self, url):
        html_fp = self.get_html_fp(url)

        if self.download_html(url, html_fp) < 0:
            # download failed
            return None

        # create bs object
        with open(html_fp, 'r') as fp:
            site_content = fp.read()

        soup = BeautifulSoup(site_content, 'html.parser')
        return soup

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

    def find_urls_from_html(self, html):
        pass

    def cleanup(self):
        self.driver.quit()


def main(url):
    # sanity check on input url
    if not SimpleWebCrawler.is_url(url):
        print("Invalid url given. Please try again with a valid url.")
        sys.exit(-1)

    # run webcrawler
    wc = SimpleWebCrawler(url)
    wc.search()

    if DEBUG:
        # stop execution here
        sys.exit(0)

    # print urls found
    print(f"Found {wc.urls_found} unique URLs:")
    for found_url in wc.url_array:
        print(found_url)

    wc.cleanup()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Incorrect number of arguments. Correct format: python3 webcrawler.py <url>")

#!/usr/bin/env python

"""
A Python program which takes in a starting URL and traverses all links found,
and their links and so on, to obtain 100 unique URLs.
"""

import os
import sys
import shutil
from pathlib import Path
from urllib.parse import urlparse

import tldextract
import numpy as np
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup, SoupStrainer


# number of unique urls to download
TARGET_URLS = 100

# name of temp dir to store html files
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
        """
        Call this function to start the URL search process from start_url.

        :return: None
        """
        self.__search_url(self.start_url, inc_searched=False)

    def __search_url(self, url_to_search, inc_searched=True):
        """
        Searches the given URL for links, then recursively searches the links found
        until TARGET_URLS number of URLs have been recorded.

        :param url_to_search: Valid URL to scrape for links
        :param inc_searched: Whether to increment url_searched
        :return: None
        """
        link_soup = self.__get_html_link_soup(url_to_search)

        if link_soup is not None:
            # find all links in the soup
            self.__find_urls(link_soup)

            if self.urls_found == TARGET_URLS:
                # stop search
                return

        # update pointer to next found url to search
        if inc_searched:
            self.urls_searched += 1

        if self.urls_found == self.urls_searched:
            print("ERROR: Ran out of links to search from")
            return

        # search the next url in the list
        self.__search_url(self.url_array[self.urls_searched])

    def cleanup(self):
        """
        Quits the Selenium driver.

        :return: None
        """
        self.driver.quit()

    # ============= Helper methods =============

    def __get_html_fp(self, url):
        """
        Returns a file path to store the HTML obtained from the given URL.

        :param url: A valid URL
        :return: Path object
        """
        filename = f"{tldextract.extract(url).domain}-{self.urls_searched}.html"
        return self.html_dir / filename

    def __download_html(self, url, html_fp):
        """
        Uses Selenium and Firefox to download the HTML code from the given URL,
        and writes it to html_fp.

        :param url: URL to download HTML from
        :param html_fp: Path to write HTML code to
        :return: 0 on success, -1 if error
        """
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

    def __get_html_link_soup(self, url):
        """
        Downloads HTML from the given URL and parses it using BeautifulSoup,
        filtering it to leave only the <a> tags.

        :param url: URL to parse
        :return: BeautifulSoup object
        """
        html_fp = self.__get_html_fp(url)

        if self.__download_html(url, html_fp) < 0:
            # download failed
            return None

        with open(html_fp, 'r') as fp:
            site_content = fp.read()

        # create soup object
        # only keep <a> tags
        soup = BeautifulSoup(site_content, 'html.parser', parse_only=SoupStrainer("a"))
        return soup

    @staticmethod
    def __get_valid_urls(link_soup):
        """
        Checks the given BeautifulSoup object for 'href' attributes containing valid URLs
        and collates the URLs into a list. link_soup is assumed to only contain <a> tags.

        :param link_soup: BeautifulSoup object containing only <a> tags
        :return: List of valid URLs
        """
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

    def __find_urls(self, link_soup):
        """
        Obtains an array of unique links from link_soup and stores them into url_array.
        If the total number of links found exceeds TARGET_URLs, it only stores the first
        n links needed to reach the target number, in the order they were found. Updates
        urls_found accordingly.

        link_soup is assumed to only contain <a> tags.

        :param link_soup: BeautifulSoup object containing only <a> tags
        :return: None
        """
        links = self.__get_valid_urls(link_soup)
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


# ===========================
#      Helper functions
# ===========================


def is_url(cand_str):
    """
    Returns True if cand_str is a properly-formatted URL.

    :param cand_str: String
    :return: Boolean
    """
    parse_result = urlparse(cand_str)
    return parse_result.scheme != "" and parse_result.netloc != ""


def get_np_arrlen(arr):
    """
    Returns the length of a 1-dimensional numpy array.

    :param arr: numpy array
    :return: int
    """
    return arr.shape[0]


# ===========================
#        Main program
# ===========================


def main(url):
    # sanity check on input url
    if not is_url(url):
        print("Invalid url given. Please try again with a valid url.")
        sys.exit(-1)

    wc = SimpleWebCrawler(url)
    wc.search()

    print(f"Found {wc.urls_found} unique URLs:")
    for i, found_url in enumerate(wc.url_array):
        print(f"{i + 1}. {found_url}")

    wc.cleanup()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Incorrect number of arguments. Correct format: python3 webcrawler.py <url>")

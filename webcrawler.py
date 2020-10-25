
import sys
import numpy as np

# number of unique urls to download
TARGET_URLS = 100


class SimpleWebCrawler:
    def __init__(self, url):
        self.start_url = url

        self.url_array = np.empty(shape=TARGET_URLS, dtype=str)
        self.urls_found = 0
        self.urls_searched = 0

    def search(self):
        # start search from start_url
        self.search_url(self.start_url, inc_searched=False)

    def search_url(self, url_to_search, inc_searched=True):
        # open url_to_search to download html

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

    def find_urls_from_html(self, html):
        pass


def main(url):
    # sanity check on input url

    # run webcrawler
    wc = SimpleWebCrawler(url)
    wc.search()

    # print urls found
    print(f"Found {TARGET_URLS} unique URLs:")
    for found_url in wc.url_array:
        print(found_url)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Incorrect number of arguments. Correct format: python3 webcrawler.py <url>")

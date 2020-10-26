# simple-webcrawler
A Python program which takes in a starting URL and traverses all links found, and their links and so on, to obtain 100 unique URLs.

## Getting started
1. Clone this repository and set up a Python virtual environment. 
2. Activate your virtual environment. 
3. Install the dependencies listed in `requirements.txt` (see note).
4. Within the repo directory, run `python3 -m webcrawler <starting_url>`. The URLs found will be printed to console.

### Note
This program uses Selenium and Firefox to fetch webpages' HTML. Hence you will need to download the latest version of geckodriver from the <a href="https://github.com/mozilla/geckodriver/releases">official release page</a> and add it to your PATH. Naturally, you will also need to have Firefox installed on your PC.

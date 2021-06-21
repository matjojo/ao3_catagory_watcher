import datetime
import time
from itertools import count

import json
from typing import Optional


import requests
from bs4 import BeautifulSoup

TIMEOUT_TIME = 10
SLEEP_TIME = 0

# login token, should probably be updated
COOKIES = {
    "_otwarchive_session": r"a3docUNaL2JNcmg0djFmSG44WC9VdXZ4aFE0bVhBd0VBMDBiaitIOGE0RWw5dWQ5eUwvckd6cXF1UmpVUXRlSzhOUHg1c1BoK3FrcUpvT0JZdkpJTVNEaUlnRmYveTFtcG00VDZhN2djK25EMktOY1NjZzliQUZJd3plbnc1bWErUWlzM1llemFCVVBzb1A5aUNYY0ZxRkx3ZDZkeXZGTXE3MFlsQURiS2VSZW1lcW9heW0wOEdUZXJ6VC9wT1NPNC9zbUpLdUwwcGc5cFdWRlRGNlQ0eVpYbkgxZEtVSGE4am1NNGVVcFpRTnpWU0xTY2Rpbm1VaGt4SVlHUFh1dWdVUzEyelNHTzZ6Z2V0bDNrNUJ2MHFOc3VobHRmMFBML1RkUlJMc3VDR2NxV1NiUlA2UGNMVmY3bldBSlNMR1EtLUZoWTczOXJNYk9NNjFrYXB1aW10a2c9PQ%3D%3D--4abda9dbb323f84f20fbc851c27324344276e0ae",
    "user_credentials": r"1",
    "view_adult": r"true",
    "accepted_tos": "20180523"}

def get_url(base_url: str, page: int) -> str:
    return base_url + str(page)


def get_page(url: str, tries: int = 5) -> Optional[requests.Response]:
    try:
        global SLEEP_TIME
        data = requests.get(url, timeout=TIMEOUT_TIME, cookies=COOKIES)
        if data.status_code == 429:
            SLEEP_TIME = SLEEP_TIME + 5
            time.sleep(30 if 30 > SLEEP_TIME else SLEEP_TIME)
            return get_page(url, tries=tries)
        if SLEEP_TIME < 30:
            SLEEP_TIME += 5
        return data
    except requests.exceptions.RequestException as e:  # for any fault
        if tries == 1:
            print(f"ERROR: was not able to reach {url} due to exception {e}")
            return None
        return get_page(url, tries=tries - 1)


def url_from_heading(heading: BeautifulSoup) -> Optional[str]:
    try:
        return heading.find("a")["href"]
    except KeyError:
        return None


def is_last_page(page_data: requests.Response) -> bool:
    page_soup = BeautifulSoup(page_data.content, "html.parser")

    nexts: list[BeautifulSoup] = page_soup.find_all("li", ["next"])

    for pot_next in nexts:
        if pot_next.find("a") is not None:
            return False

    return True

def print_one_line(element: BeautifulSoup):
    print(element.prettify().replace("\n", ""))

def card_is_title_card(card: BeautifulSoup) -> bool:
    return "id" in card.attrs and \
            card.attrs["id"].startswith("work_")

def story_cards(page_soup: BeautifulSoup) -> list[BeautifulSoup]:
    headings: list[BeautifulSoup] = page_soup.find_all("li", attrs={"role": "article"})
    
    return [header for header in headings if card_is_title_card(header)]

def get_urls_from_file() -> list[str]:
    with open("urls.txt") as urlsfile:
        return urlsfile.readlines()

class story():
    base_url = "https://archiveofourown.org"
    
    def __init__(self, card: BeautifulSoup):
        self.card = card
        
    def url(self) -> Optional[str]:
        try:
            return story.base_url + self.card.div.h4.a["href"]
        except (AttributeError, KeyError) as e:
            print(f"Could not extract url from story card due to {e}. ({self.one_line_card_str()})")

    def one_line_card_str(self) -> str:
        return self.card.prettify().replace("\n", "")

    def words(self) -> Optional[int]:
        try:
            return int(self.card.dl.find_all("dd", ["words"])[0].text.replace(",", "").replace(".", ""))
        except (AttributeError, KeyError, IndexError, ValueError) as e:
            print(f"Could not extract wordcount from story card due to {e}. ({self.one_line_card_str()})")


def save_obj_to_file(obj: dict[str, int]):
    with open("urldict.json", "w+") as f:
        json.dump(obj, f)

def get_url_to_wordcount_dict() -> dict[str, Optional[int]]:
    try:
        with open("urldict.json", "r") as f:
            return json.load(f)
    except ValueError as e:
        print("Failed to read url dict from file! (Re-raising to prevent removing urls_to_wordcount.)")
        raise e

def get_gallery_url_dict() -> dict[str, str]:
    try:
        with open("name_to_url.json", "r") as f:
            return json.load(f)
    except ValueError as e:
        print("Failed to read gallery url dict from file! (Re-raising to prevent issues downstream.)")
        raise e

if __name__ == '__main__':
    print(f"Starting check at {datetime.datetime.now()}")
    print("Now reading wordcount dictionary...")
    urls_to_wordcount: dict[str, Optional[int]] = get_url_to_wordcount_dict()
    print(f"Read {len(urls_to_wordcount)} wordcounts.")
    print("Now reading gallery urls...")
    name_to_url: dict[str, str] = get_gallery_url_dict()
    print(f"Read {len(name_to_url)} gallery urls")
    
    new_urls: list[str] = []
    for url_name, base_url in name_to_url.items():
        print(f"Now searching for {url_name}...")
        known_urls_in_this_search = 0
        for page_number in count(start=1):
            url = get_url(base_url, page_number)
    
            page_data = get_page(url)
            if page_data is None:
                print(f"  page_data == none! (for page {url}) Exiting...")
                break
    
            soup = BeautifulSoup(page_data.content, 'html.parser')
            urls_found_on_this_page = 0
            known_urls_on_this_page = 0
            for story_card in story_cards(soup):
                st = story(story_card)
                url = st.url()
                words = st.words()
                if words is None: print(f"  Words for url {url} is None!")
                # register a new url
                # cannot read / empty wordcount, assume changed
                # register a changed story
                if url not in urls_to_wordcount or            \
                        urls_to_wordcount[url] != words or    \
                        words is None:
                    urls_to_wordcount[url] = words
                    new_urls.append(url)
                else:
                    # nothing changed
                    known_urls_in_this_search += 1
                    known_urls_on_this_page += 1
                urls_found_on_this_page += 1
    
    
            print(f"  Parsed page {page_number}, got {urls_found_on_this_page} urls. (changed: {len(new_urls)}, unchanged: {known_urls_in_this_search})")
            
            if is_last_page(page_data):
                print("  That was the last page.")
                break
            
            if known_urls_on_this_page == 20:
                print(f"  We've found {known_urls_on_this_page} stories that haven't changed on this page. Assuming done...")
                break
            
            # don't want to scare the servers
            time.sleep(SLEEP_TIME)
    
    save_obj_to_file(urls_to_wordcount)
    print("Saved known urls to file.")
    if new_urls:
        print("Appending new urls to file...")
        try:
            with open("undownloaded.txt", "a") as f:
                for url in new_urls:
                    f.write(url)
                    f.write("\n")
        except IOError:
            print("Failed to write urlss:")
            for url in new_urls:
                print(url)
    
    print(f"Finished check at {datetime.datetime.now()}")
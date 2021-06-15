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
    "_otwarchive_session": "ekJLVlYza25rY0Q3cWozbGZVK1RWWjd2cDgrS3J3dXBFbmlZb0Qwb2drZW41Sml4T21xdm96T3lOZjFlVDF6c0k1SHFObHZqMjFBQ3RTSkpQdHY0YTV5ZVY4YnVhVngyVGEwbUx6bFlkby9LQXEySnE4TWNsQ0lxYUpTYXZZaitnQjNnaVBZbjliMXhVZ2dTM25qWFRQbzJ1YkdyaDJMUmVpSlZhRUNPdXpPSlhKOHEzWGp6TFdFdEQyb3NjSVoySVRJMlpqUDVRUVRHTUl4dFdCUVpCQmlpRHl0enhENkM1YnRqV09NcWRkTE8yT1dSdkZZZFV1amJ1b1kvWUExWmc0eWNBSEVpZVdORjBaMzN4WWtCeG92T1RkM1dCV1JUM210SU9MdS9URXJJMEF1SHVJZktsU1BLUVl1SUJ3VTF4L3phQS9LS0piYTF1MDRWait1MXJodGNkVk10Y0NJelZLTVRuUEhSN3pRPS0tZCtwcEpFbnZQVXljWm9HRXhrbDIwZz09--19fa8bf8a01b128d688e908880f3c03cc9f0d3fe",
    "user_credentials": "1"}

BASE_URLS_WITH_NAME = []

FROZEN_BASE_URL    = "https://archiveofourown.org/tags/Frozen%20(Disney%20Movies)/works?page="
BASE_URLS_WITH_NAME.append((FROZEN_BASE_URL, "Frozen"))

LISTRANGE_BASE_URL = "https://archiveofourown.org/tags/Life%20Is%20Strange%20(Video%20Game)/works?page="
BASE_URLS_WITH_NAME.append((LISTRANGE_BASE_URL, "Life Is Strange"))


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

if __name__ == '__main__':
    print("Now reading wordcount dictionary...")
    urls_to_wordcount: dict[str, Optional[int]] = get_url_to_wordcount_dict()
    print("Read wordcount dictionary.")
    
    new_urls: list[str] = []
    for base_url, url_name in BASE_URLS_WITH_NAME:
        print(f"Now searching for {url_name}...")
        known_urls_in_this_search = 0
        for page_number in count(start=1):
            url = get_url(base_url, page_number)
    
            page_data = get_page(url)
            if page_data is None:
                print(f"page_data == none! (for page {url}) Exiting...")
                break
    
            soup = BeautifulSoup(page_data.content, 'html.parser')
            urls_found_on_this_page = 0
            known_urls_on_this_page = 0
            for story_card in story_cards(soup):
                st = story(story_card)
                url = st.url()
                words = st.words()
                
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
    
    
            print(f"Parsed page {page_number}, got {urls_found_on_this_page} urls. (changed: {len(new_urls)}, unchanged: {known_urls_in_this_search})")
            
            if is_last_page(page_data):
                print("That was the last page. Writing to file now...")
                break
            
            if known_urls_on_this_page > 10:
                print(f"We've found {known_urls_on_this_page} stories that haven't changed on this page. Assuming done...")
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

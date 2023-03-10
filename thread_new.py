import csv
import json
import sys
import threading
import time
from datetime import datetime
import requests
import requests_html
import pyppeteer.errors
from requests_html import HTMLSession
from random import randint
from typing import List, Dict, Tuple, Any, Generator
from parsing_tools_3 import get_authors_by_letter, Author
from auxiliary_tools import get_headers
from config import PROC_STOP_MSG, URL, NA_SIGN


def get_main_response_and_check_200(url: str, lang: str) -> Any:
    headers = get_headers(fake_user_agent=True)
    langs = {"en": "", "be": "/be", "ru": "/ru"}
    link = url + langs[lang]
    session = HTMLSession()
    response = session.get(link, headers=headers)
    if response.status_code == 200:
        return response
    print(f"[ERROR] Response is not OK (status code is not 200). Check the URL.{PROC_STOP_MSG}")


def get_response_per_scroll(response: Any, lang: str) -> Any:
    language = {"en": "English", "be": "Belarusian", "ru": "Russian"}
    time.sleep(randint(1, 2))
    print(f"\nStart scrolling in {language[lang]}...")
    js_out = {'result': 0}
    counter = -1
    scrolls = 5
    scroll_height = 300
    while js_out['result'] == 0:
        js_script_down = f'(function down() {{let y={counter}; for(let i={scrolls}*y;i<{scrolls}*(y+1);i++) ' \
                     f'{{if ((window.scrollY + window.innerHeight) >= document.body.scrollHeight) {{' \
                     f'return {{result: 1, coordinates: window.pageYOffset}}; }};' \
                     f'window.scrollTo(0, i*{scroll_height});' \
                     f'}};' \
                     f'return {{result: 0, coordinates: window.pageYOffset}}' \
                     f'}})()'
        counter += 1
        try:
            js_out = response.html.render(timeout=30, sleep=2, script=js_script_down)
            print(f"Scrolling {counter}: {js_out}")
        except pyppeteer.errors.TimeoutError as pyTE:
            pyTE_msg = f"{pyTE}\nIn the 'render()' function, you should set bigger volume to 'timeout=' (20 seconds by default).{PROC_STOP_MSG}"
            print(f"[ERROR] {pyTE_msg}")
            sys.exit()
        except Exception as exc:
            print(f"888 [ERROR] {exc}")
            sys.exit()
        else:
            yield response


def get_all_authors_list_lang(response, lang: str) -> List[Author]:
    all_authors_list_lang = []
    for next_response in get_response_per_scroll(response, lang):
        authors_per_scroll = get_authors_by_letter(next_response, lang)
        for author in authors_per_scroll:
            is_author_in_list = False
            for author_in_all_authors in all_authors_list_lang:
                if author_in_all_authors.link == author.link:
                    author_in_all_authors.__dict__[f"name_{lang}"] = author.__dict__[f"name_{lang}"]
                    is_author_in_list = True
                    break
            if not is_author_in_list:
                all_authors_list_lang.append(author)
    return all_authors_list_lang


def get_author_content(lang, all_authors_thread):
    url = URL
    response = get_main_response_and_check_200(url, lang)
    print(lang, response)
    all_authors_list_lang = get_all_authors_list_lang(response, lang)
    all_authors_thread.append(all_authors_list_lang)
    return("responsed" + lang)


def main():
    all_authors_thread = []
    threads = []
    for lang in ['en', 'be', 'ru']:
        thread = threading.Thread(target=get_author_content, args=[lang, all_authors_thread])
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    print(all_authors_thread)

def main_simple():
    all_authors_thread = []
    lang = 'en'
    get_author_content(lang, all_authors_thread)
    print(all_authors_thread)

if __name__ == "__main__":
    main()
    # main_simple()


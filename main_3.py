import csv
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple, Any, Generator
from random import randint
import pyppeteer.errors
import requests
import requests_html
from requests_html import HTMLSession
from parsing_tools_3 import get_authors_by_letter, get_author_events, get_event_data, Author
from config import PROC_STOP_MSG, URL, NA_SIGN
from auxiliary_tools import timer, get_headers, show_dict_as_json, create_temp_file, get_author_content_from_json_file
import logging.config
from settings import logger_config


logging.config.dictConfig(logger_config)
logger = logging.getLogger('logger')


def get_main_response_and_check_200(url: str, lang: str) -> Any:
    """ Take an url and return response object if response status is 200 [OK].
    """
    headers = get_headers(fake_user_agent=True)
    langs = {"en": "", "be": "/be", "ru": "/ru"}
    link = url + langs[lang]
    try:
        session = HTMLSession()
        response = session.get(link, headers=headers)
    except requests.exceptions.RequestException as reRE:
        print(f"[ERROR] {reRE}{PROC_STOP_MSG}")
        logger.exception(f"{reRE}{PROC_STOP_MSG}")
        sys.exit()
    if response.status_code == 200:
        return response
    print(f"[ERROR] Response is not OK (status code is not 200). Check the URL.{PROC_STOP_MSG}")


def get_response_per_scroll(response: Any, lang: str) -> Any:
    """ Take the response and provide JS script during 'render()' function.
        Script performs (imitates) 'scrolls' amount per every script execution.
        'js_out' is script's output that contain new coordinate of scrolled page bottom
        and result ("1" - if the main page's bottom is reached, "0" - in other case).
        When "1", return response object.
    """
    language = {"en": "English", "be": "Belarusian", "ru": "Russian"}
    time.sleep(randint(1, 2))
    print(f"\nStart scrolling in {language[lang]}...")
    js_out = {'result': 0}
    counter = -1  # Started from '-1' to load first unscrolled page (usually from '0')
    scrolls = 5   # Amount of scrolls per script execution = per render()
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
            logger.exception(pyTE_msg)
            sys.exit()
        except Exception as exc:
            print(f"[ERROR] {exc}")
            logger.exception(exc)
        else:
            yield response


def get_all_authors_list_lang(all_authors_list: List, response, lang: str) -> List[Author]:
    """ Add authors to the list of authors by specified language.
        If author already in list, add name in specified language to author's data.
        Return list of author objects collected by language.
    """
    for next_response in get_response_per_scroll(response, lang):
        authors_per_scroll = get_authors_by_letter(next_response, lang)
        for author in authors_per_scroll:
            is_author_in_list = False
            for author_in_all_authors in all_authors_list:
                if author_in_all_authors.link == author.link:
                    author_in_all_authors.__dict__[f"name_{lang}"] = author.__dict__[f"name_{lang}"]
                    is_author_in_list = True
                    break
            if not is_author_in_list:
                all_authors_list.append(author)
    return all_authors_list


def check_missed_names(all_authors_list: List) -> None:
    """ Find authors without EN, BE or RU name. Open author's page by link
        and get name if exists, then change None to the name or "N/A (EN name)".
    """
    print("\nStart filling missed names...")
    headers = get_headers(fake_user_agent=True)
    session = requests_html.HTMLSession()
    langs = {"en": "", "be": "/be", "ru": "/ru"}
    count = 1
    for author in all_authors_list:
        if not all((author.name_en, author.name_be, author.name_ru)):
            for lang in ("en", "be", "ru"):
                if author.__dict__[f"name_{lang}"] is None:
                    author_link = author.link.replace("/names", f"{langs[lang]}/names")
                    resp = session.get(url=author_link, headers=headers)
                    try:
                        author_name = resp.html.find("h1[class*='post-title translation-view']", first=True).text
                    except AttributeError:
                        author_name = f"{NA_SIGN} ({author.name_en})"
                    author.__dict__[f"name_{lang}"] = author_name
                    print(f'[INFO] Author #{count} added: name_{lang} = {author.__dict__[f"name_{lang}"]!r}')
            count += 1


def add_events_to_author(author: Author) -> Author:
    """ Get an author without events and add all events to it.
        Return the author, ready to be saved.
    """
    author_link = author.link
    headers = get_headers(fake_user_agent=True)
    author_events, session_2 = get_author_events(author_link, headers)
    for event in author_events:
        event_data = get_event_data(event, session_2, headers)
        author.events.append(event_data)
    return author


def get_author_content() -> Generator[Tuple[Author, int], None, None]:
    """ Prepare the entire author's content (data + events) to save.
    """
    url = URL
    all_authors_list: List[Author] = []

    for lang in ("en", "be", "ru"):
        response = get_main_response_and_check_200(url, lang)
        all_authors_list = get_all_authors_list_lang(all_authors_list, response, lang)
        create_temp_file(all_authors_list)

    # Function fixes the issues with: NOVA, ???????????? ??????????, Michael Veksler, Tasha Arlova
    check_missed_names(all_authors_list)
    create_temp_file(all_authors_list)

    count_authors = len(all_authors_list)
    msg_collected = f"{count_authors} author{'s are' if count_authors > 1 else ' is'} collected from the site."
    print(f"[INFO] {msg_collected}")
    logger.info(msg_collected)

    for author in all_authors_list:
        add_events_to_author(author)
        yield author, count_authors     # Author is full and ready to store


def save_content_to_json(source: str = "internet") -> None:
    """ Get author as object of class Author, then convert it to the dict
        and add it to the list of all authors.
        Finally, increased list of all authors save to the json file. """
    if source == "file":
        print("Scanning data from file...")
        archive_file = "LA_all_authors_FULL.json"
        time.sleep(2)
        author_content = get_author_content_from_json_file(archive_file)
    else:
        author_content = get_author_content()

    date_time = datetime.now().strftime("%Y.%m.%d__%H:%M")
    filename = f"LA_{date_time}.json"
    all_authors_as_dicts__list = []
    count = 0

    for data in author_content:
        if count == 0:
            print(f"\nStart saving authors to file {filename!r}...")
            time.sleep(3)


        author, authors_amount = data

        author_in_dict = author.author_obj_into_dict()
        all_authors_as_dicts__list.append(author_in_dict)
        count += 1
        print(f"[INFO] {count}/{authors_amount} Author {author.name_en!r} executed")
        with open(filename, "w", encoding='utf-8') as json_file:
            json.dump(all_authors_as_dicts__list, json_file, indent=4, ensure_ascii=False)

    if source == "file":
        logger.info(f"{authors_amount} author{'s are' if authors_amount > 1 else ' is'} collected from the archive file {archive_file!r}.")

    logger.info(f"{authors_amount} author{'s are' if authors_amount > 1 else ' is'} added to the {filename!r}.")


def save_content_to_csv(source: str = "internet") -> None:
    """ Get author as object of class Author, then convert it to the dict
        and finally write to the csv file with mode "a".
        When the first author, his dict keys are field names for file. """
    if source == "file":
        print("Scanning data from file...")
        archive_file = "LA_all_authors_FULL.json"
        time.sleep(2)
        author_content = get_author_content_from_json_file(archive_file)
    else:
        author_content = get_author_content()

    date_time = datetime.now().strftime("%Y.%m.%d__%H:%M")
    filename = f"LA_{date_time}.csv"
    count = 0

    for data in author_content:
        if count == 0:
            print(f"\nStart saving authors to file {filename!r}...")
            time.sleep(3)

        author, authors_amount = data
        author_in_dict = author.author_obj_into_dict()

        with open(filename, "a", encoding='utf-8') as csv_file:
            if count == 0:
                author_keys = author_in_dict.keys()
                field_names = [i for i in author_keys]

            csv_writer = csv.DictWriter(csv_file, fieldnames=field_names)

            csv_writer.writeheader()
            csv_writer.writerow(author_in_dict)

        count += 1
        print(f"[INFO] {count}/{authors_amount} Author {author.name_en!r} executed")


    if source == "file":
        logger.info(
            f"{authors_amount} author{'s are' if authors_amount > 1 else ' is'} collected from the archive file {archive_file!r}.")

    logger.info(f"{authors_amount} author{'s are' if authors_amount > 1 else ' is'} added to the {filename!r}.")


@timer
def mainthread() -> None:
    print("[INFO] Process started =>")
    logger.info("Process started =>")
    save_content_to_json(source="file")
    # save_content_to_csv(source="file")


if __name__ == '__main__':
    mainthread()
    print("=== Process finished successfully! ===")
    logger.info("=> Process finished successfully!\n")

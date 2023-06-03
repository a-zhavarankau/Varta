import multiprocessing
import sys
import time
import requests
import pyppeteer.errors
from requests_html import HTMLSession
from random import randint
from typing import List, Dict, Tuple, Any
from parsing_tools_4 import get_authors_by_letter, Author
from auxiliary_tools_4 import get_headers, create_temp_file_json
from config import PROC_STOP_MSG, URL, URL_END, SCROLLS, SCROLL_HEIGHT
import logging.config
from settings import logger_config


logging.config.dictConfig(logger_config)
logger = logging.getLogger('logger')


def get_main_response_and_check_200(url: str, url_end: str, lang: str) -> requests.Response:
    """ Take an url and return response object if response status is 200 [OK].
    """
    headers = get_headers(fake_user_agent=True)
    langs = {"en": "", "be": "/be", "ru": "/ru"}
    link = url + langs[lang] + url_end

    try:
        session = HTMLSession()
        response = session.get(link, headers=headers)
    except requests.exceptions.RequestException as reRE:
        print(f"[ERROR] {reRE}{PROC_STOP_MSG}")
        logger.exception(f"{reRE}{PROC_STOP_MSG}")
        sys.exit()
    if response.status_code == 200:
        return response
    else:
        not_200_msg = f"Response from {lang.upper()!r} is not OK (status code is not 200). Check the URL.{PROC_STOP_MSG}"
        print(f"[ERROR] {not_200_msg}")
        logger.error(not_200_msg)
        sys.exit()



def get_response_per_scroll(response: Any, lang: str) -> Any:
    """ Take the response and provide JS script during 'render()' function.
        Script performs (imitates) 'scrolls' amount per every script execution.
        'js_out' is script's output that contain new coordinate of scrolled page bottom
        and result ("1" - if the main page's bottom is reached, "0" - in other case).
        When "1", return response object.
    """
    language = {"en": "English", "be": "Belarusian", "ru": "Russian"}
    time.sleep(randint(1, 2))
    print(f"Start scrolling in {language[lang]}...")
    js_out = {'result': 0}
    counter = -1  # Started from '-1' to load first unscrolled page (usually from '0')
    scrolls = SCROLLS   # Amount of scrolls per script execution = per render()
    scroll_height = SCROLL_HEIGHT
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
            print(f"{lang.upper()!r} Scrolling {counter}: {js_out}")
        except pyppeteer.errors.TimeoutError as pyTE:
            pyTE_msg = f"{pyTE}\nIn the 'render()' function, you should set bigger volume to 'timeout=' (20 seconds by default).{PROC_STOP_MSG}"
            print(f"[ERROR] {pyTE_msg}")
            logger.exception(pyTE_msg)
            sys.exit()
        except Exception as exc:
            print(f"[ERROR] {exc}")
            logger.exception(exc)
            sys.exit()
        else:
            yield response


def get_authors_by_lang(lang: str) -> Tuple[str, List[Author]]:
    """ Get responses per scroll and create list of all
        authors in specified language.
    """
    url = URL
    url_end = URL_END
    response = get_main_response_and_check_200(url, url_end, lang)
    print(f"{lang.upper()!r}", response)
    all_authors_list_lang = []
    for next_response in get_response_per_scroll(response, lang):
        authors_per_scroll = get_authors_by_letter(next_response, lang)
        for author in authors_per_scroll:
            if author not in all_authors_list_lang:
                all_authors_list_lang.append(author)
    return lang, all_authors_list_lang


def get_multiproc_authors_by_langs() -> List[Tuple[str, List[Author]]]:
    """ Start authors collection in 3 languages simultaneously
        with 'multiprocessing' module.
    """
    print("\nStart collecting authors without events (multiprocessing)...")
    with multiprocessing.Pool(processes=3) as pool:
        authors_lists_by_langs = pool.map(get_authors_by_lang, ['en', 'be', 'ru'])
        pool.close()
        pool.join()

    print("Multiprocessing finished successfully")
    return authors_lists_by_langs


def put_multiproc_authors_in_dict(authors_lists_by_langs) -> Dict[str, List[Author]]:
    """ Create a dict = {'language': 'list of authors'}.
        We need this function to keep parsing process under control.
    """
    authors_dict = {}
    logger.info(f"{SCROLLS=}, {SCROLL_HEIGHT=}")
    for data in authors_lists_by_langs:
        lang, authors_list_by_lang = data
        authors_dict[lang] = authors_list_by_lang
        create_temp_file_json(authors_list_by_lang, filename=f"MAlist_{lang}")
        lang_auth_msg = f"In lang {lang.upper()!r} are {len(authors_list_by_lang)} authors"
        logger.info(lang_auth_msg)
        print(lang_auth_msg)
    return authors_dict


def main_multiproc():
    assert sys.version_info >= (3, 7), "Script requires Python 3.7+."

    ### (1/5) Get list containing 3 lists of authors in EN/BE/RU
    authors_lists_by_langs = get_multiproc_authors_by_langs()
    ### (2/5) Put 3 authors lists into dict
    authors_all_langs_in_dict = put_multiproc_authors_in_dict(authors_lists_by_langs)
    return authors_all_langs_in_dict


if __name__ == "__main__":
    res = main_multiproc()
    print(res)

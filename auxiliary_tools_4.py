import os
import json
import fake_useragent
from datetime import datetime
from parsing_tools_4 import Author
from typing import List, Dict, Tuple, Callable, Generator


def timer(func: Callable) -> Callable:
    def wrap(*args, **kwargs):
        start = datetime.now()
        res = func(*args, **kwargs)
        time = datetime.now() - start
        print(f"[Timer information] Function {func.__name__!r} executed in time: {str(time)[:7]}")
        return res
    return wrap


def get_headers(fake_user_agent: bool = False) -> Dict[str, str]:
    """ Returns headers containing fake useragent if agrument 'fake_user_agent'=True
        (default=False), else original useragent.
    """
    fake_user = fake_useragent.UserAgent().random
    original_user = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
                    "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                  "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "User-Agent": fake_user if fake_user_agent else original_user,
    }
    return headers


def show_dict_as_json(dict_: Dict) -> json:
    return json.dumps(dict_, indent=4, ensure_ascii=False)


def create_temp_file_json(all_authors_list: List,
                          filename: str = "TEMP_all_authors") -> None:
    all_authors_for_json = [author.author_obj_into_dict() for author in all_authors_list]

    temp_folder = create_folder("temp")
    with open(f"{temp_folder}/{filename}.json", "w", encoding='utf-8') as jf:
        json.dump(all_authors_for_json, jf, indent=4, ensure_ascii=False)


def create_folder(dir_name: str) -> str:
    dir_path = os.path.join(os.getcwd(), dir_name)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    return dir_path

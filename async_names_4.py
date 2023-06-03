import asyncio
import aiohttp
from multiproc_authors_4 import main_multiproc
from typing import List, Dict
from parsing_tools_4 import Author, text_handler
from auxiliary_tools_4 import get_headers, create_temp_file_json
from bs4 import BeautifulSoup as bs
from config import NA_SIGN
import logging.config
from settings import logger_config


logging.config.dictConfig(logger_config)
logger = logging.getLogger('logger')


def create_all_authors_list(authors_all_langs_in_dict: Dict[str, List[Author]]) -> List[Author]:
    """ Create list of all authors from dict of authors lists
        in different languages (separately) and fill in every
        author with names in EN/BE/RU languages from that dict.
    """
    all_authors_list = []
    for lang in authors_all_langs_in_dict:
        for author_lang in authors_all_langs_in_dict[lang]:
            is_author_in_list = False
            for author in all_authors_list:
                if author_lang == author:
                    author.__dict__[f"name_{lang}"] = author_lang.__dict__[f"name_{lang}"]
                    is_author_in_list = True
                    break
            if not is_author_in_list:
                all_authors_list.append(author_lang)
    return all_authors_list


async def check_author_names_async(author: Author, asession) -> None:
    """ Find authors without EN, BE or RU name (for ex.: NOVA, Шестая линия,
        Michael Veksler, Tasha Arlova). Open author's page by link and get name
        [if exists], then change None to the name [or "N/A (EN name)"].
    """
    langs = {"en": "", "be": "/be", "ru": "/ru"}
    if not all((author.name_en, author.name_be, author.name_ru)):
        for lang in ("en", "be", "ru"):
            if author.__dict__[f"name_{lang}"] is None:
                author_link = author.link.replace("/in/names", f"{langs[lang]}/in/names")
                async with asession.get(author_link) as resp:
                    # for i in range(1, 6):
                    #     try:
                    #         author_apage = await resp.text()
                    #     except asyncio.exceptions.TimeoutError as aeTE:
                    #         print(f"Issue happened: {aeTE} (attempt #{i}")
                    #         if i == 5:
                    #             print(PROC_STOP_MSG)
                    #             sys.exit()
                    #     else:
                    #         break
                    author_apage = await resp.text()
                    author_soup = bs(author_apage, 'lxml')
                try:
                    author_name = author_soup.find("h1", class_="post-title translation-view").text
                    author_name = text_handler(author_name)
                except AttributeError:
                    author_name = f"{NA_SIGN} ({author.name_en})"
                author.__dict__[f"name_{lang}"] = author_name
                print(f'[INFO] Author <{author.name_en}> added: name_{lang} = {author.__dict__[f"name_{lang}"]!r}')


async def check_missed_names_async(all_authors_list: List[Author]) -> None:
    """ Start function that adds missed names in EN/BE/RU to author.
    """
    print("\nStart filling missed names...")
    headers = get_headers(fake_user_agent=True)
    async with aiohttp.ClientSession(headers=headers) as asession:
        tasks = [check_author_names_async(author, asession) for author in all_authors_list]
        await asyncio.gather(*tasks)
    print("Filling missed names finished successfully")


def async_get_authors_checked_names():
    authors_all_langs_in_dict = main_multiproc()

    ### (3/5) From dict of authors in all languages create list,
    # where each author is filled in with all names in EN/BE/RU
    all_authors_list = create_all_authors_list(authors_all_langs_in_dict)
    filename = "Repair_tempfile"
    create_temp_file_json(all_authors_list, filename=filename)


    # with open(f"{filename}.json") as jf:
    #     authors_list = json.load(jf)
    #     all_authors_list = [Author.author_dict_into_obj(i) for i in authors_list]
    #     print(len(all_authors_list))

    asyncio.run(check_missed_names_async(all_authors_list))
    print()

    count_authors = len(all_authors_list)
    msg_collected = f"{count_authors} author{'s are' if count_authors > 1 else ' is'} collected from the site."
    print(f"[INFO] {msg_collected}")
    logger.info(msg_collected)

    return all_authors_list


if __name__ == "__main__":
    res = async_get_authors_checked_names()
    print(res)

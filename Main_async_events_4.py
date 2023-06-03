import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import List
from async_names_4 import async_get_authors_checked_names
from parsing_tools_4 import Author, get_author_events_without_data, get_event_data_async
from auxiliary_tools_4 import get_headers
import logging.config
from settings import logger_config


logging.config.dictConfig(logger_config)
logger = logging.getLogger('logger')


async def get_author_with_full_events_async(author, asession) -> Author:
    """ Get author and add to him all events with data.
        In the output we have a fully-filled author.
    """
    author_events_without_data: List = await get_author_events_without_data(author, asession)

    ##### asyncio.exceptions.TimeoutError
    tasks = []
    for event in author_events_without_data:
        task = asyncio.create_task(get_event_data_async(event, asession))
        tasks.append(task)
    events_with_data = await asyncio.gather(*tasks)

    len_before = len(events_with_data)
    events_with_data_cleaned = [event for event in events_with_data if event]
    len_after = len(events_with_data_cleaned)
    if len_before != len_after:
        empty_count = len_before - len_after
        msg_empty_event = f"{author.name_en!r} has {len_before - len_after} empty event{'s' if empty_count > 1 else ''}"
        print(f"===INFO=== {msg_empty_event}")
        logger.info(msg_empty_event)

    author.events = events_with_data_cleaned
    print(f"Author {author.name_en!r} is ready")
    return author


async def async_get_full_content(all_authors_list) -> List[Author]:
    """ Take list of all authors and add authors' events there.
    """
    headers = get_headers(fake_user_agent=True)
    print("\nStart collecting of authors' events...")

    async with aiohttp.ClientSession(headers=headers) as asession:
        tasks = [asyncio.create_task(get_author_with_full_events_async(author, asession)) for author in all_authors_list]
        all_authors_w_events = await asyncio.gather(*tasks)

    print("Collecting of authors' events finished successfully")
    return all_authors_w_events


def save_content_to_json(all_authors_w_events: List[Author],
                         filename: str = None) -> None:
    """ Get author as object of class Author, then convert it to the dict
        and add it to the list of all authors.
        Finally, increased list of all authors save to the json file.
    """
    if filename is None:
        date_time = datetime.now().strftime("%Y.%m.%d__%H:%M")
        filename = f"Kalektar_{date_time}.json"
    print(f"\nStart saving authors to file {filename!r}...")

    all_authors_as_dicts__list = []
    count_authors = len(all_authors_w_events)
    for author in all_authors_w_events:
        author_in_dict = author.author_obj_into_dict()
        all_authors_as_dicts__list.append(author_in_dict)
    with open(filename, "w", encoding='utf-8') as json_file:
        json.dump(all_authors_as_dicts__list, json_file, indent=4, ensure_ascii=False)

    print("Saving authors to JSON file finished")
    msg_json_added = f"{count_authors} author{'s are' if count_authors > 1 else ' is'} added to the {filename!r}"
    print(f"[INFO] {msg_json_added}")
    logger.info(msg_json_added)


if __name__ == "__main__":
    assert sys.version_info >= (3, 7), "Script requires Python 3.7+."
    print("Process started =>")
    start = datetime.now()

    all_authors_list = async_get_authors_checked_names()

    ### (4/5) Get full authors' content
    all_authors_w_events = asyncio.run(async_get_full_content(all_authors_list))
    ### (5/5) Save content
    save_content_to_json(all_authors_w_events)

    msg_finish_success = f"=> Process finished successfully!\nAsync time: {datetime.now() - start}\n"
    print("\n", msg_finish_success)
    logger.info(msg_finish_success)


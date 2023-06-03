import sys
import asyncio
import random
from bs4 import BeautifulSoup as bs
from typing import List, Dict, Any, Optional, Union, Generator
from config import PROC_STOP_MSG, NA_SIGN, URL


class Author:
    def __init__(self, link: str, name_en: Optional[str] = None, name_be: Optional[str] = None,
                 name_ru: Optional[str] = None, occupation: Optional[str] = None,
                 source: Optional[str] = None, events: Optional[List[Dict]] = None):
        self.link = link
        self.name_en = name_en
        self.name_be = name_be
        self.name_ru = name_ru
        self.occupation = occupation
        self.source = source or URL
        self.events = events if events and isinstance(events, list) else []

    def author_obj_into_dict(self) -> Dict[str, Union[str, Optional[str], Optional[List[Dict]]]]:
        """ Convert Author instance to the dict with all fields ordered
        """
        key_order = ('name_en', 'name_be', 'name_ru', 'occupation', 'link', 'source', 'events')
        author_dict = dict((k, self.__dict__[k]) for k in key_order)
        return author_dict

    def __str__(self):
        return str(self.author_obj_into_dict())

    def __eq__(self, other) -> bool:
        # Changed to perform  comparison with old links (early: 'self.link == other.link')
        return self.link.split("/")[-1] == other.link.split("/")[-1]

    @staticmethod
    def author_dict_into_obj(author_dict: Dict[str, Union[str, Optional[str], Optional[List[Dict]]]]):
        """ Convert dict to the Author instance
        """
        author = Author(**author_dict)
        return author


def get_letter_block(response: Any) -> Generator:
    letter_blocks = response.html.find("section.observable-section")
    for letter_block in letter_blocks:
        yield letter_block


def get_authors_by_letter(response: Any, lang: str) -> Generator[Author, None, None]:
    """ Yield an object of class Author (which contains all data except 'events')
        from the letter block.
    """
    for letter_block in get_letter_block(response):
        authors_in_letter = letter_block.find("div[class*='cell-box cell-box-feed public']")
        for author_block in authors_in_letter:
            author_name = author_block.find("span.title", first=True).text
            author_occupation = author_block.find("div[class*='short-description desc']", first=True).text
            author_token = author_block.find("a.post-link-box", first=True).links
            author_link = f"https://kalektar.org{author_token.pop()}"

            # Make all 'author_link' without "be" and "ru" attachments
            author_link = author_link.replace("/ru", "") if "/ru" in author_link else author_link.replace("/be", "")
            author = Author(link=author_link, occupation=author_occupation)
            author.__dict__[f"name_{lang}"] = author_name
            yield author


# Need to handle errors
async def get_author_events_without_data(author: Author, asession) -> List:
    """ Collect all events from author. Return list of events in HTML.
    """
    author_link = author.link
    await asyncio.sleep(round(random.uniform(0.5, 1.5), 1))
    try:
        async with asession.get(author_link) as resp:
            apage = await resp.text()
    except Exception as exc:
        print(f"Exception occured: {exc}\n{PROC_STOP_MSG}")

        sys.exit()

    soup = bs(apage, 'lxml')
    events = soup.findAll("div", class_="cell-box cell-box-ref public event")
    return events


# NEED TO HANDLE EXCEPTION
async def get_event_data_async(event, asession) -> Dict[str, str]:
    """ Return dict containing event data: name, dates,
        place, link.
    """
    event_token = event.find("a", class_="post-link-box").get("href")
    event_link = "https://kalektar.org" + event_token
    await asyncio.sleep(0.5)

    ##### asyncio.exceptions.TimeoutError
    async with asession.get(event_link) as resp:
        event_apage = await resp.text()
        event_soup = bs(event_apage, 'lxml')
    try:
        event_name = event_soup.find("h1", class_="post-title translation-view").text
        event_name = text_handler(event_name)
    except AttributeError:
        event_name = NA_SIGN

    try:
        event_dates_block = event_soup.find("span", class_="dates-string inline-block")
        event_dates = " ".join([text_handler(date.text) for date in event_dates_block])
    except (AttributeError, TypeError):
        event_dates = NA_SIGN

    try:
        event_place = event_soup.find("div",
            class_="translation-editor-view").text
    except AttributeError:
        try:
            event_place = event_soup.find("div",
            class_="translation-auto-view").text
        except AttributeError:
            try:
                event_place = event_soup.find("div",
            class_="translation-undefined-view").text
            except AttributeError:
                event_place = NA_SIGN

    event_place = text_handler(event_place)

    event_name_dict = {'event_name': event_name}
    if event_name == NA_SIGN:
        print("Empty event")
        return None
    event_dates_dict = {'event_dates': event_dates}
    event_place = event_place.replace("\xa0\xa0\xa0", ";")
    event_place_dict = {'event_place': event_place}
    event_link_dict = {'event_link': event_link}
    event_dict = event_name_dict | event_dates_dict | event_place_dict | event_link_dict
    return event_dict


def text_handler(text: str) -> str:
    """ Check text for unwanted symbol and change it.
        Examples: "Text\ntranslation" -> "Text (translation)";
                  "\n NOVA \n " -> "NOVA".
    """
    text = text.strip("\n ")
    if "\n" in text:
        text = text.replace("\n", " (") + ")"
    return text

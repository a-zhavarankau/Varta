##Varta 

###Description
It's a startup project focused on art. Developer task is to parse the defined sites ("https://kalektar.org/") to get the following information:
- Author name, occupation
- Author's events (name, dates, place, links)
<br><br>

###Instrunemts:
- asyncio, aiohttp
- multiprocessing
- requests
- requests_html
- JavaScript
- Burp Suite

###How to run
Launch file "Main_async_events_4.py". All the actions will be displayed in the 'run' window. When the script has finished there will be the file "Kalektar_[date]_[time].json" containing all the data parsed from the site.
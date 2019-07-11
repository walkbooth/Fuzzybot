import sys
import json
from datetime import datetime, timezone, timedelta
from re import search
from urllib3 import PoolManager 
from discord_webhook import DiscordWebhook

def main ():

    # Read from StreetFoodFinder
    http = PoolManager()
    url = 'https://streetfoodfinder.com/fuzzysempanadas'
    response = http.request('GET', url)

    # Scrape calendar from response
    events_string = search(r"sff\.v\.vendor_locations = (.*);", response.data.decode('utf-8')).group(1).replace('null', '""')
    if not events_string:
        print("Unable to parse events from http response")
        sys.exit(1)
    events = json.loads(events_string)

    # Generate message from events
    message = "**Fuzzy's Empanadas Immediate Calendar**"
    for event in events:
        date, starttime = datetime.fromtimestamp(event['starttime'], timezone(timedelta(hours=-4)) ).strftime('%Y-%m-%d %H:%M:%S').split()
        endtime = datetime.fromtimestamp(event['endtime'], timezone(timedelta(hours=-4)) ).strftime('%Y-%m-%d %H:%M:%S').split()[1]
        message += "\n\t{}: @ {} from {} to {}".format(date, event['fulladdress'], starttime, endtime)

    # Send the generated calender message to #food-as-a-service
    print("Sending the following message to #food-as-a-service...")
    print(message)
    webhook = DiscordWebhook(url=open('webhook', 'r').read(), content=message)
    webhook.execute()

# Call main
main()
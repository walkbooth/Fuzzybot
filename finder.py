import sys
import json
from datetime import datetime, timezone, timedelta
from re import search
from urllib3 import PoolManager 
from discord_webhook import DiscordWebhook

FOODTRUCKS_URL = 'https://streetfoodfinder.com/'
GOOGLEMAPS_URL = 'https://www.google.com/maps/dir/'

def main ():

    # Read from StreetFoodFinder
    http = PoolManager()
    truck_id = 'fuzzysempanadas'
    response = http.request('GET', FOODTRUCKS_URL + truck_id)

    # Scrape calendar from response
    events_string = search(r'sff\.v\.vendor_locations = (.*);', response.data.decode('utf-8')).group(1).replace('null', '""')
    if not events_string:
        print('Unable to parse events from http response')
        sys.exit(1)
    events = json.loads(events_string)

    # Generate message from events
    message = ":fuzzys: **Fuzzy's Empanadas Upcoming Events** :fuzzys:"
    for event in events:
        date, starttime = datetime.fromtimestamp(event['starttime'], timezone(timedelta(hours=-4)) ).strftime('%Y-%m-%d %H:%M:%S').split()
        endtime = datetime.fromtimestamp(event['endtime'], timezone(timedelta(hours=-4)) ).strftime('%Y-%m-%d %H:%M:%S').split()[1]
        date = date[5:].replace('-','/')
        starttime = starttime[:5]
        endtime = endtime[:5]

        source = '5200+Paramount+Parkway'
        destination = event['shortstreet'].replace(' ', '+')
        response_text = http.request('GET', GOOGLEMAPS_URL + source + '/' + destination).data.decode('utf-8')

        distance = search(r'([\d|\.]* miles)', response_text).group(1)
        time = search(r'(\d+ min)', response_text).group(1)
        message += '\n\t{}: @ {}, {} ({}) away. Event from {} to {}'.format(date, event['shortstreet'], distance, time, starttime, endtime)

    # Send the generated calender message to #food-as-a-service
    print('Sending the following message to #food-as-a-service...')
    print(message)
    webhook = DiscordWebhook(url=open('webhook', 'r').read(), content=message)
    webhook.execute()

# Call main
main()
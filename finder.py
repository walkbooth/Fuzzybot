"""
Script to locate food trucks from StreetFoodFinder.
"""

import sys
import json
from datetime import datetime, timezone, timedelta
from re import search
import argparse
import requests
from discord_webhook import DiscordWebhook
from bs4 import BeautifulSoup
import googlemaps


def readkey(key):
    """
    Read a key from the 'apikeys' directory
    """
    with open(f"apikeys/{key}") as stream:
        key_contents = stream.read()
    return key_contents


# URLs used for HTTP requests
FOODTRUCKS_URL = "https://streetfoodfinder.com/"

# Location to route from
SOURCE = "5200 Paramount Parkway"

# Google maps client object
GMAPS = googlemaps.Client(key=readkey("maps"))


def get_args():
    """
    Parse arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="run without sending a message to the discord channel",
    )
    parser.add_argument(
        "format", choices=["daily", "weekly"], help="specify format of message"
    )
    parser.add_argument(
        "-l",
        "--location",
        default="5200 Paramount Parkway",
        help="specify a source location to measure distance from truck",
    )

    return parser.parse_args()


def get_events():
    """
    Reads and returns a list of events from StreetFoodFinder
    """

    # Read from StreetFoodFinder
    truck_id = "thenakedempanada"
    response = requests.get(FOODTRUCKS_URL + truck_id)

    # Scrape calendar from response (located in JS variable "var" defined below)
    soup = BeautifulSoup(response.text, "html.parser")
    var = r"sff\.v\.vendor_locations"
    events_string = ""
    for tag in soup.find_all("script"):
        if tag.string:
            match = search(f"{var} = (.*);", tag.string)
            if match:
                events_string = match.group(1).replace("null", '""')

    if not events_string:
        print("Unable to parse events from HTTP response")
        sys.exit(1)

    return json.loads(events_string)


def format_event(event, source):
    """
    Adds new keys to event dictionary object resulting from GET request
    """
    event["start_datetime"] = datetime.fromtimestamp(
        event["starttime"], timezone(timedelta(hours=-4))
    )
    event["date"], event["starttime"] = (
        event["start_datetime"].strftime("%m/%d %H:%M").split()
    )
    event["endtime"] = datetime.fromtimestamp(
        event["endtime"], timezone(timedelta(hours=-4))
    ).strftime("%H:%M")

    directions_result = GMAPS.directions(
        source,
        event["streetaddress"],
        mode="driving",
        departure_time=event["start_datetime"],
    )

    event["distance"] = directions_result[0]["legs"][0]["distance"]["text"]
    event["traveltime"] = directions_result[0]["legs"][0]["duration"]["text"]
    return event


def event_tostring(event):
    """
    Gets string version of an event dictionary (result of format_event)
    """
    return (
        f"@ {event['shortstreet']}, {event['distance']} ({event['traveltime']}) away. Event "
        f"from {event['starttime']} to {event['endtime']}"
    )


def build_daily_message(events, source):
    """
    Construct the Discord message following the 'daily' message format.
    """
    message = (
        "**!!!     __EmpanadaBot Alert__     !!!**\n\n"
        "_In the next 24 hours, The Naked Empanada is..._"
    )
    event_tomorrow = False
    for event in events:
        event = format_event(event, source)
        if event["start_datetime"] - timedelta(days=1) < datetime.now(
            event["start_datetime"].tzinfo  # pylint: disable=bad-continuation
        ):
            event_tomorrow = True
            message += f"\n\t {event['date']} {event_tostring(event)}"
        else:
            break
    if not event_tomorrow:
        message += "\n\tnot scheduled :("
    return message


def build_weekly_message(events, source):
    """
    Construct the Discord message following the 'daily' message format.
    """
    message = (
        "**!!!     __EmpanadaBot Alert__     !!!**\n\n"
        "_The Naked Empanada Upcoming Events..._"
    )
    for event in events:
        event = format_event(event, source)
        if event["start_datetime"] - timedelta(days=7) < datetime.now(
            event["start_datetime"].tzinfo  # pylint: disable=bad-continuation
        ):
            message += f"\n\t{event['date']}: {event_tostring(event)}"
    return message


def send_to_discord(message):
    """
    Sends a message to the discord channel pointed to in the webhook file
    """
    webhook = DiscordWebhook(url=readkey("discord"), content=message)
    print(f"{message}\nSending the above message to #food-as-a-service...")
    webhook.execute()
    print("Message sent!")


def main():
    """
    Parse arguments and construct message based on desired behavior
    """
    args = get_args()
    events = get_events()

    if args.format == "daily":
        message = build_daily_message(events, args.location)
        print(message)

    elif args.format == "weekly":
        message = build_weekly_message(events, args.location)
        print(message)

    # Send the generated calender message to #food-as-a-service
    if not args.debug:
        send_to_discord(message)


# Call main
main()

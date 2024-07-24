# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import requests
from nyct_gtfs import NYCTFeed
from nyct_gtfs.compiled_gtfs import gtfs_realtime_pb2
from datetime import datetime, timedelta
import pytz
import pandas as pd

from flask import Flask
from flask import jsonify

app = Flask(__name__)

stop_id_to_station_name = {}
direction_to_bound = {
    'N': "Northbound",
    'E': "Eastbound",
    'S': "Southbound",
    'W': "Westbound",
}

# def create_stop_json_array():
#     lines = [
#         "ACE",
#         "BDFM",
#         "G",
#         "L",
#         "JZ",
#         "NQRW",
#         "123",
#         "456",
#         "7",
#         "S"
#     ]
#     subway_line_dict = {}
#     for subway_line in lines:
#         subway_line_dict[subway_line] = []
#         get_all_stops_by_subway_line(subway_line)
#         for stop in


def get_train_info(station_code):
    # URL for GTFS real-time feed (you need to replace this with the actual MTA GTFS URL)
    url = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs'

    # Make a request to the GTFS real-time data feed
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(url, headers={"x-api-key": "your_api_key_here"})
    feed.ParseFromString(response.content)

    # print(feed.entity[0])

    now = datetime.now(pytz.utc)

    # Iterate through the feed entities and check for train updates
    print("Arrival times for station: " + stop_id_to_stop_name(station_code))
    for direction in ['N', 'S', 'E', 'W']:
        mins_til = []
        directional_station_code = station_code + direction
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip_update = entity.trip_update
                for stop_time_update in trip_update.stop_time_update:
                    if stop_time_update.stop_id == directional_station_code:
                        arrival_time = datetime.fromtimestamp(stop_time_update.arrival.time, pytz.utc)
                        time_difference = arrival_time - now
                        seconds_until_arrival = int(time_difference.total_seconds())
                        minutes_until_arrival = int(time_difference.total_seconds() / 60)

                        # print(entity)

                        # print(trip_update.trip)
                        trip_id = trip_update.trip.trip_id
                        trip_id_number = get_trip_id_number(trip_id)
                        route_id = trip_update.trip.route_id
                        obj = {
                            'trip_id': trip_id,
                            'route_id': route_id,
                            'minutes_until_arrival': minutes_until_arrival
                        }
                        mins_til.append(obj)

                        gtfs_stop_id = trip_number_and_route_to_gtfs_stop(trip_id_number, route_id)

                        # stop_name = stop_id_to_stop_name(gtfs_stop_id)
        mins_til.sort(key=lambda x: x['minutes_until_arrival'])
        
        pos_mins_til = []
        for m in mins_til:
            if m['minutes_until_arrival'] > 0:
                pos_mins_til.append(m)
        
        return pos_mins_til

        # for m in mins_til:
        #     print(
        #         f"{direction_to_bound[direction]} {m['route_id']} Train: Arrives in {m['minutes_until_arrival']} minutes")

def get_trip_id_number(trip_id):
    return trip_id.split('..')[1][1:3]

def trip_number_and_route_to_gtfs_stop(trip_id_number, route_id):
    # should be 3 digits; digit 1 is train name and digits 2 and 3 are stop #, e.g. D42
    combo = str(route_id) + str(trip_id_number)
    return combo

def stop_id_to_stop_name(stop_id):
    if stop_id in stop_id_to_station_name:
        return stop_id_to_station_name[stop_id]
    else:
        return "Unknown Station"

def trip_id_to_stop_id(trip_id):
    return trip_id.split('..')[1][:3]

def load_trip_to_station_dict(csv_file):
    # Load the CSV file
    data = pd.read_csv(csv_file)

    # Map GTFS Stop ID to Stop Name
    global stop_id_to_station_name
    stop_id_to_station_name = pd.Series(data['Stop Name'].values, index=data['GTFS Stop ID']).to_dict()


def get_all_stops_by_subway_line(subway_line):
    """
        ACCEPTABLE VALUES (as strings)
        - ACE
        - BDFM
        - NQRW
        - JZ
        - L
        - 123
        - 456
        - 7
        - G
    """
    df = pd.read_csv("stations.csv")
    for char in subway_line:
        filtered_df = df[df['Daytime Routes'].str.contains(char, na=False)]
        # print(filtered_df[['Borough', 'Stop Name', 'Daytime Routes', 'GTFS Stop ID']])
        return filtered_df[['Borough', 'Stop Name', 'Daytime Routes', 'GTFS Stop ID']]


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


def print_hi():
    # Use a breakpoint in the code line below to debug your script.
    # print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.
    # feed = NYCTFeed("1", api_key='')
    # trains = feed.filter_trips(line_id=["1", "2", "3"], headed_for_stop_id=["127N", "127S"], underway=True)
    # print(str(trains[0]))

    station_code = '635'  # Replace with actual station code
    print(get_train_info(station_code))

def run_on_startup():
    load_trip_to_station_dict("stations.csv")
    print_hi()

def prod():
    run_on_startup()

if __name__ == '__main__':
    prod()
    # print(get_all_stops_by_subway_line('456'))


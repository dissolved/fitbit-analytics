# Fitbit API docs: https://dev.fitbit.com/docs/
# fitbit-python docs: http://python-fitbit.readthedocs.io/en/latest/

from datetime import date, timedelta
from dateutil.parser import parse
# from ratelimit import rate_limited
# import fire
import fitbit
import json
import os

DATA_DIR = "intraday_data"

def refresh_tokens(dict):
    with open('tokens.json') as token_file:
        tokens = json.load(token_file)

    print("Refreshing tokens!")
    tokens["ACCESS"] = dict["access_token"]
    tokens["REFRESH"] = dict["refresh_token"]
    with open('tokens.json', 'w') as token_file:
        json.dump(tokens, token_file)

def get_client():
    with open('tokens.json') as token_file:
        tokens = json.load(token_file)
    return fitbit.Fitbit(tokens["KEY"], tokens["SECRET"],
                         access_token = tokens["ACCESS"],
                         refresh_token = tokens["REFRESH"],
                         refresh_cb = refresh_tokens)

def write_data(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f)


class Retriever:
    def __init__(self):
        self.client = get_client()

    def retrieve(self, start_date):
        if type(start_date) == str:
            start_date = parse(start_date).date()

        yesterday = date.today() - timedelta(1)
        delta = date.today() - start_date
        activities = ('steps','floors','elevation','distance','calories')

        for day in (yesterday - timedelta(n) for n in range(delta.days)):
            self.get_sleep(day)
            self.get_heart(day)
            for resource in activities:
                self.get_intraday(resource = "activities/{}".format(resource),
                             date = day)

    def get_intraday(self, resource = 'activities/steps', date = date.today()):
        path = os.path.join(DATA_DIR, resource, str(date) + '.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
        else:
            data = self.fetch_intraday(resource, date)
            write_data(data, path)

        return data


    def fetch_intraday(self, resource = 'activities/steps', date = date.today()):
        print("Retrieving {} intraday for {}".format(resource, date))
        return self.client.intraday_time_series(resource, base_date = date)


    def get_sleep(self, date):
        path = os.path.join(DATA_DIR, 'sleep', str(date) + '.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
        else:
            data = self.fetch_sleep(date)
            write_data(data, path)

        return data


    def fetch_sleep(self, date):
        print("Retrieving sleep data for {}".format(date))
        return self.client.get_sleep(date)


    def get_heart(self, date):
        path = os.path.join(DATA_DIR, 'heart', str(date) + '.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
        else:
            data = self.fetch_heart(date)
            write_data(data, path)

        return data


    def fetch_heart(self, date):
        print("Retrieving heart rate data for {}".format(date))
        return self.client.time_series('activities/heart',
                                        base_date = date, period = '1d')

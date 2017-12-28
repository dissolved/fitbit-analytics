# Fitbit API docs: https://dev.fitbit.com/docs/
# fitbit-python docs: http://python-fitbit.readthedocs.io/en/latest/

from datetime import date, timedelta
from dateutil.parser import parse
from ratelimit import rate_limited
import fire
import fitbit
import json
import os

DATA_DIR = "intraday_data"
HOURLY_API_LIMIT = 150

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


def get_intraday(client, resource = 'activities/steps', date = date.today()):
    path = os.path.join(DATA_DIR, resource, str(date) + '.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
    else:
        data = fetch_intraday(client, resource, date)
        write_data(data, path)

    return data


def fetch_intraday(client, resource = 'activities/steps', date = date.today()):
    print("Retrieving {} intraday for {}".format(resource, date))
    return client.intraday_time_series(resource, base_date = date)


def get_sleep(client, date):
    path = os.path.join(DATA_DIR, 'sleep', str(date) + '.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
    else:
        data = fetch_sleep(client, date)
        write_data(data, path)

    return data


def fetch_sleep(client, date):
    print("Retrieving sleep data for {}".format(date))
    return client.get_sleep(date)


def get_heart(client, date):
    path = os.path.join(DATA_DIR, 'heart', str(date) + '.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
    else:
        data = fetch_heart(client, date)
        write_data(data, path)

    return data


def fetch_heart(client, date):
    print("Retrieving heart rate data for {}".format(date))
    return client.time_series('activities/heart', base_date = date,
                                                  period = '1d')


def retrieve(start_date):
    client = get_client()
    if type(start_date) == str:
        start_date = parse(start_date).date()

    yesterday = date.today() - timedelta(1)
    delta = date.today() - start_date
    activities = ('steps','floors','elevation','distance','calories')

    if len(activities)*delta.days > HOURLY_API_LIMIT:
        global fetch_intraday
        global fetch_sleep
        global fetch_heart
        fetch_intraday = rate_limited(3*HOURLY_API_LIMIT - 1, 7200)(fetch_intraday)
        fetch_sleep = rate_limited(3*HOURLY_API_LIMIT - 1, 7200)(fetch_sleep)
        fetch_heart = rate_limited(3*HOURLY_API_LIMIT - 1, 7200)(fetch_heart)

    for day in (yesterday - timedelta(n) for n in range(delta.days)):
        get_sleep(client, day)
        get_heart(client, day)
        for resource in activities:
            get_intraday(client,
                        resource = "activities/{}".format(resource),
                        date = day)

if __name__ == '__main__':
  fire.Fire({
      'retrieve': retrieve
  })

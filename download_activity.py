# Fitbit API docs: https://dev.fitbit.com/docs/
# fitbit-python docs: http://python-fitbit.readthedocs.io/en/latest/

from datetime import date, timedelta
from ratelimit import rate_limited
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


def save_intraday(data, path):
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
        save_intraday(data, path)

    return data


@rate_limited(150,3600)
def fetch_intraday(client, resource = 'activities/steps', date = date.today()):
    print("Retrieving {} intraday for {}".format(resource, date))
    return client.intraday_time_series(resource, base_date = date)


if __name__ == '__main__':
    client = get_client()

    start_date = date(2013, 1, 5)
    delta = date.today() - start_date
    for day in (start_date + timedelta(n) for n in range(delta.days)):
        data = get_intraday(client, resource = 'activities/calories', date = day)

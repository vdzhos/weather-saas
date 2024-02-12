from datetime import datetime, timezone
import json

import requests
from flask import Flask, jsonify, request

API_TOKEN = ""
WEATHER_API_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Welcome to Weather App.</h2></p>"


@app.route("/content/api/v1/integration/weather", methods=["POST"])
def weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    if json_data.get("requester_name") is None:
        raise InvalidUsage("requester name is required", status_code=400)

    if json_data.get("location") is None:
        raise InvalidUsage("location is required", status_code=400)

    if json_data.get("date") is None:
        raise InvalidUsage("date is required", status_code=400)

    token = json_data.get("token")
    requester_name = json_data.get("requester_name")
    location = json_data.get("location")
    date = json_data.get("date")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    weather = get_weather(location,date)

    current_utc_datetime = datetime.now(timezone.utc)
    timestamp = current_utc_datetime.isoformat(timespec='seconds').replace('+00:00', 'Z')

    result = {
        "requester_name": requester_name,
        "timestamp": timestamp,
        "location": location,
        "date": date,
        "weather": weather
    }

    return result

def get_weather(location, date):
    url_base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"

    url = f"{url_base_url}/{location}/{date}?unitGroup=metric&key={WEATHER_API_KEY}"

    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        all_info = json.loads(response.text)
        result = {
            "temp_c": all_info['days'][0]['temp'],
            "wind_kph": all_info['days'][0]['windspeed'],
            "pressure_mb": all_info['days'][0]['pressure'],
            "humidity": all_info['days'][0]['humidity']
        }
        return result
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)

# Weather API meteomatics

import datetime as dt
import meteomatics.api as api
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap5
import requests
import json

app = Flask(__name__)


# ------------------------------- Date todays -----------------------------------
def generate_today_date():
    """Returns the today's date in format Month DD, YYYY

    Returns:
        string: Month DD, YYYY
    """
    today = dt.datetime.now()
    month = today.strftime("%B")
    day = today.strftime("%d")
    year = today.strftime("%Y")
    return f"{month} {day}, {year}"


# ------------------------------- METEOMATICS API -----------------------------------
def get_weather_data(location, parameters):
    """Get the latitude and longitude based on user's input' and pass them as coordinates.

    Args:
        location (dict): a dictionary that contains latitude and longitude as keys.
        parameters (list): a list of the desired parameters for the API query.

    Returns:
        pd.DataFrame: a DataFrame that contains the API response.
    """
    latitude = location["latitude"]
    longitude = location["longitude"]
    coordinates = [(latitude, longitude)]
    startdate = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    enddate = startdate + dt.timedelta(days=1)
    interval = dt.timedelta(hours=1)

    df = api.query_time_series(
        coordinates,
        startdate,
        enddate,
        interval,
        parameters,
        METEOMATICS_API_USERNAME,
        METEOMATICS_API_PASSWORD,
        model="mix",
    )
    df = df.reset_index()
    return df


# ------------------------------- FLASK WTF -----------------------------------
class MyWeatherForm(FlaskForm):
    location = StringField(label="City location", validators=[DataRequired()])
    country_code = StringField(
        label="Country code (two letters)",
        description="If you are not sure of your country code please check "
        "it <a href= 'https://www.iban.com/country-codes', target = '_blank'>here</a>. ",
        validators=[DataRequired()],
    )
    submit = SubmitField(label="Check Weather")


# ------------------------------- LOCATION COORDINATES -----------------------------------
def get_coordinates(location, country_code):
    """Use of the Geocoding API through OpenWeatherMap to get the latitude and logitude coordinates
    based on user's writen location.

    Args:
        location (str): A string containing the name of a city (e.g. Barcelona)
        country_code (str): A string containing the country code in two letters (e.g. ES)

    Returns:
        dict: a dictionary that contains latitude and longitude as keys.
    """
    city_name = location
    limit = 1
    URL = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&limit={limit}&appid={OPEN_WEATHER_API_KEY}"
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()
    coordination_result = {"latitude": data[0]["lat"], "longitude": data[0]["lon"]}
    return coordination_result


# ------------------------------- WEBSITE ROUTES -----------------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    """Flask function defining the root for the app.

    Returns:
        str: HTML of the rendered webpage.
    """
    form = MyWeatherForm()
    if request.method == "GET":
        return render_template("index.html", form=form, date=generate_today_date()[14:])
    if form.validate_on_submit():
        location = form.location.data
        country_code = form.country_code.data
        coordinates_location = get_coordinates(
            location=location, country_code=country_code
        )

        general_parameters = [
            "t_3m:C",
            "precip_1h:mm",
            "relative_humidity_3m:p",
            "wind_speed_3m:kmh",
            "uv:idx",
            "sunrise:sql",
            "sunset:sql",
            "dust_0p03um_0p55um:ugm3",
        ]

        specific_parameters = [
            "birch_pollen:grainsm3",
            "grass_pollen:grainsm3",
            "olive_pollen:grainsm3",
            "ragweed_pollen:grainsm3",
        ]

        weather_df_basic = get_weather_data(
            location=coordinates_location, parameters=general_parameters
        )

        weather_df_specific = get_weather_data(
            location=coordinates_location, parameters=specific_parameters
        )

        return render_template(
            "weather.html",
            user_location=location,
            weather_df_basic=weather_df_basic,
            weather_df_specific=weather_df_specific,
            weather_date=generate_today_date(),
            date=generate_today_date()[14:],
        )


if __name__ == "__main__":
    bootstrap = Bootstrap5(app)

    # ------------------------------- API KEYS -----------------------------------
    with open("credentials.json", "r") as file:
        credentials = json.load(file)
    app.config["SECRET_KEY"] = credentials["flask_secret_key"]
    METEOMATICS_API_USERNAME = credentials["meteomatics_api_username"]
    METEOMATICS_API_PASSWORD = credentials["meteomatics_api_password"]
    OPEN_WEATHER_API_KEY = credentials["openweather_api_key"]
    app.run(debug=True)

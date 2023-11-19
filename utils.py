import requests
from config import WEATHER_TOKEN


photo_count_per_user = {}


async def send_weather(lat, lon) -> dict:
    lat = round(lat, 2)
    lon = round(lon, 2)
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_TOKEN}&lang=uk"
            f"&units=metric"

        )
        data = r.json()
        return data
    except Exception as ex:
        print(ex)
        print("Щось пішло не так =(")


async def weather_info_parser(data: dict):
    new_data = {'опис': data['weather'][0]['description']}
    pressure = str(data['main']['pressure'] / 1.333)
    new_data['тиск'] = pressure[:3] + " мм."
    new_data['температура'] = str(data['main']['temp'])[:2]
    return new_data

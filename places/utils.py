import requests
from django.conf import settings
from django.utils import timezone

from places.models import Place
from star_burger.custom_errors import YandexApiError


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    except Exception:
        raise YandexApiError('Ошибка определения координат ресторана (со стороны Yandex)')

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def save_place(address):
    place, _ = Place.objects.get_or_create(address=address)
    try:
        place_coordinates = fetch_coordinates(
            settings.YANDEX_API_KEY,
            address
        )
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException):
        place.latitude = place.longitude = None
        place.update_time = timezone.now()
        place.save()
        return

    if not place_coordinates:
        place.latitude = place.longitude = None
        place.update_time = timezone.now()
        place.save()
        return

    place.latitude, place.longitude = place_coordinates
    place.save()

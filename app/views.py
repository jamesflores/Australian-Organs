from django.shortcuts import render
import requests
from django.conf import settings


def index(request):
    context = {
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY
    }
    return render(request, 'map/map.html', context)
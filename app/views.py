from django.shortcuts import render
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


def index(request):
    context = {
        'ORGAN_API_URL': settings.ORGAN_API_URL,
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        'domain': request.scheme + '://' + get_current_site(request).domain
    }
    return render(request, 'map/map.html', context)


def search(request):
    context = {
        'ORGAN_API_URL': settings.ORGAN_API_URL,
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        'domain': request.scheme + '://' + get_current_site(request).domain,
    }
    return render(request, 'map/search.html', context)
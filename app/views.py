from django.shortcuts import render
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


def index(request):
    domain = request.scheme + '://' + get_current_site(request).domain
    context = {
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        'domain': domain
    }
    return render(request, 'map/map.html', context)
from django.shortcuts import render
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django_ratelimit.decorators import ratelimit

from .models import URLRedirect
from urllib.parse import unquote


def index(request):
    context = {
        'ORGAN_API_URL': settings.ORGAN_API_URL,
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        'domain': request.scheme + '://' + get_current_site(request).domain
    }
    return render(request, 'map/home.html', context)


def map(request):
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


@ratelimit(key='ip', rate='10/m')   # Limit to 10 requests per minute per IP address
def redirect(request):
    if getattr(request, 'limited', False):
        return HttpResponse('Too many requests', status=429)
    url = unquote(request.GET.get('url', ''))
    URLRedirect.hit(url)
    return HttpResponseRedirect(url)
from django.shortcuts import render
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, MagicLink, URLRedirect
from django.utils import timezone
from urllib.parse import unquote
from django.contrib.auth.decorators import login_required


def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('app'))
    
    return render(request, 'map/home.html')


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


@login_required(login_url='/login/')
def app_view(request):
    return render(request, 'map/app.html')


@ratelimit(key='ip', rate='10/m')   # Limit to 10 requests per minute per IP address
def redirect(request):
    if getattr(request, 'limited', False):
       return HttpResponse('Too many requests', status=429)
    url = unquote(request.GET.get('url', ''))
    URLRedirect.hit(url)
    return HttpResponseRedirect(url)


def request_magic_link(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user, created = CustomUser.objects.get_or_create(email=email)
        magic_link = MagicLink.objects.create(user=user)
        
        # send email with magic link
        send_mail(
            'Your magic link to log into Australian Organs',
            f'Click here to log in: {request.build_absolute_uri("/login/")}?token={magic_link.token}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return render(request, 'map/magic_link_sent.html')
    
    return render(request, 'map/request_magic_link.html')


def login_with_magic_link(request):
    # check if already logged in
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('app'))
    
    token = request.GET.get('token')
    if not token:
        return HttpResponseRedirect(reverse('request_magic_link'))
    
    # check if magic link is valid
    try:
        magic_link = MagicLink.objects.get(token=token)
        if magic_link.is_valid():
            login(request, magic_link.user)
            magic_link.delete()
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'map/invalid_magic_link.html')
    except MagicLink.DoesNotExist:
        return render(request, 'map/invalid_magic_link.html')
    

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))

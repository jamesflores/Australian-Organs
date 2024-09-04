import json
from operator import itemgetter
from django.forms import ValidationError
from django.shortcuts import render
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.conf import settings
import requests
from .models import Bookmark, CustomUser, MagicLink, URLRedirect
from django.utils import timezone
from urllib.parse import unquote
from django.contrib.auth.decorators import login_required
from django_q.tasks import async_task


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


def organ_page(request, organ_id):
    # Fetch organ page from the API
    response = requests.get(f'{settings.ORGAN_API_URL}/organ/render/{organ_id}/')
    if response.status_code == 200:
        organ_data = response.json()
        try:
            page_data = organ_data[0]['html']
        except Exception as e:
            page_data = "No data available"
    else:
        return render(request, 'map/organ_detail.html', {'page_data': "No data available"})

    # Fetch organ details from the API
    response = requests.get(f'{settings.ORGAN_API_URL}/organ/{organ_id}/')
    if response.status_code == 200:
        organ_data = response.json()
        try:
            organ_name = organ_data['results'][0]['name']
            organ_description = organ_data['results'][0]['description']
            organ_address = organ_data['results'][0]['address']
            organ_state = organ_data['results'][0]['state']
            organ_city = organ_data['results'][0]['city']
            organ_postcode = organ_data['results'][0]['postcode']
            organ_builder = organ_data['results'][0]['builder']
            organ_main_image = organ_data['results'][0]['main_image']
            organ_lat = organ_data['results'][0]['latitude']
            organ_lon = organ_data['results'][0]['longitude']
            organ_url = organ_data['results'][0]['url']
        except Exception as e:
            return render(request, 'map/organ_detail.html', {'page_data': "No data available"})
    else:   
        return render(request, 'map/organ_detail.html', {'page_data': "No data available"})
    
    context = {
        'page_data': page_data,
        'organ_id': organ_id,
        'organ_name': organ_name,
        'organ_description': organ_description,
        'organ_address': organ_address,
        'organ_state': organ_state,
        'organ_city': organ_city,
        'organ_postcode': organ_postcode,
        'organ_builder': organ_builder,
        'organ_main_image': organ_main_image,
        'organ_lat': organ_lat,
        'organ_lon': organ_lon,
        'url': request.build_absolute_uri(),
        'source_url': organ_url,
    }

    # Render the organ page
    return render(request, 'map/organ_detail.html', context)


@login_required(login_url='/login/')
def app_view(request):
    bookmarks = Bookmark.objects.filter(user=request.user)
    organs = []

    for bookmark in bookmarks:
        # Fetch organ details from the API
        response = requests.get(f'{settings.ORGAN_API_URL}/organ/{bookmark.organ_id}/')
        if response.status_code == 200:
            organ_data = response.json()
            if organ_data['results']:
                organs.append(organ_data['results'][0])

    # Sort the organs list by name
    sorted_organs = sorted(organs, key=itemgetter('name'))

    return render(request, 'map/app.html', {'organs': sorted_organs})


@ratelimit(key='ip', rate='10/m')   # Limit to 10 requests per minute per IP address
def redirect(request):
    if getattr(request, 'limited', False):
       return HttpResponse('Too many requests', status=429)
    
    url = unquote(request.GET.get('url', ''))
    organ_id = request.GET.get('organ_id', '')

    if organ_id:  # attempt to redirect to the OrganPage view
        response = requests.get(f'{settings.ORGAN_API_URL}/organ/render/{organ_id}/')
        if response.status_code == 200:
            return HttpResponseRedirect(reverse('organ', args=[organ_id]))

    URLRedirect.hit(url)
    return HttpResponseRedirect(url)  # Redirect to the URL


@ratelimit(key='ip', rate='10/m')   # Limit to 10 requests per minute per IP address
def request_magic_link(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        error = None

        # Sanity check email
        if not email:
            error = 'Email is required'
        else:
            # Additional email validation
            try:
                validate_email(email)
                # Check for common disposable email domains
                disposable_domains = ['tempmail.com', 'throwawaymail.com', 'mailinator.com']
                domain = email.split('@')[-1]
                if domain in disposable_domains:
                    error = 'Please use a non-disposable email address'
            except ValidationError:
                error = 'Please enter a valid email address'

        if error:
            return render(request, 'map/request_magic_link.html', {'error': error})
        
        user, created = CustomUser.objects.get_or_create(email=email)
        magic_link = MagicLink.objects.create(user=user)
        
        # Send email with magic link
        async_task(
            'django.core.mail.send_mail',
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


@login_required(login_url='/login/')
def bookmark_organ(request):
    organ_id = request.GET.get('organ_id')
    if not organ_id:
        return JsonResponse({'error': 'organ_id is required'}, status=400)
    
    try:
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, organ_id=organ_id)
        
        if created:
            return JsonResponse({'message': 'Bookmark added'}, status=201)
        else:
            bookmark.delete()
            return JsonResponse({'message': 'Bookmark removed'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='/login/')
def check_bookmark(request):
    organ_id = request.GET.get('organ_id')
    if not organ_id:
        return JsonResponse({'error': 'organ_id is required'}, status=400)
    
    try:
        is_bookmarked = Bookmark.objects.filter(user=request.user, organ_id=organ_id).exists()
        return JsonResponse({
            'is_bookmarked': is_bookmarked,
            'text': '★ Saved' if is_bookmarked else '☆ Save organ to your list'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
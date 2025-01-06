from django.core.mail import EmailMessage
from operator import itemgetter
import random
from django.forms import ValidationError
from django.shortcuts import render
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.conf import settings
import requests
from .models import Bookmark, CustomUser, LoginCode
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
            return render(request, 'map/organ_detail.html', {'page_data': None })
    else:
        return render(request, 'map/organ_detail.html', {'page_data': None })

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
            return render(request, 'map/organ_detail.html', {'page_data': None })
    else:   
        return render(request, 'map/organ_detail.html', {'page_data': None })
    
    is_bookmarked = False
    if request.user.is_authenticated:
        # check to see if the organ is bookmarked
        if Bookmark.objects.filter(user=request.user, organ_id=organ_id).exists():
            is_bookmarked = True

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
        'is_bookmarked': is_bookmarked,
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
        if response.status_code == 200 and response.json() != []:
            return HttpResponseRedirect(reverse('organ', args=[organ_id]))

    return HttpResponseRedirect(url)  # Redirect to the URL
    

@ratelimit(key='ip', rate='10/m')   # Limit to 10 requests per minute per IP address
def send_login_code(request):
    # check if already logged in
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('app'))
    
    if request.method == 'POST':
        email = request.POST.get('email')
        error = None

        # Validate the email
        if not email:
            error = 'Email is required.'
        else:
            try:
                validate_email(email)
            except ValidationError:
                error = 'Please enter a valid email address.'

        if error:
            return render(request, 'login_code.html', {'error': error})

        # Get or create the user
        user, created = CustomUser.objects.get_or_create(email=email)

        # Store email in session
        request.session['login_email'] = email

        # Generate a random 6-digit code
        code = f"{random.randint(100000, 999999)}"

        # Create a new LoginCode entry
        LoginCode.objects.create(user=user, code=code)

        # Build the verification URL
        verification_url = request.build_absolute_uri(reverse('verify_login_code'))

        # Send the login code to the user's email
        async_task(
            'django.core.mail.send_mail',
            f"Your login code is: {code}",
            f"""Your login code is: {code}

Click here to verify your code:
{verification_url}""",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        # Display success message
        messages.success(request, "Login code sent to your email.")
        return HttpResponseRedirect(reverse('verify_login_code'))

    # Handle GET request: display the form
    return render(request, 'map/request_login_code.html')


def verify_login_code(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('app'))

    if request.method == "POST":
        # Get email from session instead of POST data for security
        email = request.session.get('login_email')
        code = request.POST.get("code")

        if not email:
            messages.error(request, "Session expired. Please try again.")
            return HttpResponseRedirect(reverse('login'))

        # Try to get or create the user
        user, created = CustomUser.objects.get_or_create(email=email)

        # Fetch the login code for the user
        login_code = LoginCode.objects.filter(user=user, code=code).first()

        if login_code and login_code.is_valid():
            # Clear the session email after successful login
            request.session.pop('login_email', None)
            # Log in the user
            login(request, user)
            messages.success(request, "Successfully logged in.")
            return HttpResponseRedirect(reverse('index'))
        else:
            # Invalid or expired code
            messages.error(request, "Invalid or expired login code.")
            return HttpResponseRedirect(reverse('login'))
        
    return render(request, "map/verify_login_code.html", {'email': request.session.get('login_email', '')})


def logout_view(request):
    request.session.flush()
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
    

def send_email(subject, body, from_email, recipient_list, reply_to=None):
    """
    A standalone function to send an email.
    This function is picklable and can be used with async_task.
    """
    headers = {'Reply-To': reply_to} if reply_to else {}
    email_message = EmailMessage(
        subject,
        body,
        from_email,
        recipient_list,
        headers=headers,
    )
    email_message.send()


def contact_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')  # Optional field
        message = request.POST.get('message')
        turnstile_response = request.POST.get('cf-turnstile-response')

        # Verify Cloudflare Turnstile
        turnstile_verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
        turnstile_secret = settings.CLOUDFLARE_TURNSTILE_SECRET_KEY
        response = requests.post(turnstile_verify_url, data={
            'secret': turnstile_secret,
            'response': turnstile_response,
        })
        result = response.json()
        print(result)  # Debugging log
        if not result.get('success', False):
            messages.error(request, 'Bot verification failed. Please try again.')
            return HttpResponseRedirect(reverse('contact'))

        subject = 'New Contact Form Submission'
        body = f"Email: {email}\nPhone: {phone}\n\nMessage:\n{message}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [settings.CONTACT_EMAIL]

        try:
            # Send email to the site owner
            async_task(
                send_email,
                subject,
                body,
                from_email,
                recipient_list,
                email,  # Reply-To header
            )

            # Send confirmation email to the sender
            confirmation_subject = 'Your message has been received'
            confirmation_body = (
                f'Thank you for contacting us. We have received your message and will get back to you soon.\n\n'
                f'Original message:\n{message}'
            )
            async_task(
                send_email,
                confirmation_subject,
                confirmation_body,
                from_email,
                [email],
            )

            messages.success(request, 'Thank you for your message. We will get back to you soon.')
        except Exception as e:
            messages.error(request, f'An error occurred while sending the email: {e}')

        return HttpResponseRedirect(reverse('contact'))

    return render(request, 'map/contact_form.html', {
        'site_key': settings.CLOUDFLARE_TURNSTILE_SITE_KEY,
    })
import os
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from dotenv import load_dotenv
from django_q.tasks import async_task


load_dotenv()

class Command(BaseCommand):
    help = 'Send test email'

    def handle(self, *args, **options):
        subject = 'Test Email'
        message = 'This is a test email.'
        from_email = os.getenv('DEFAULT_FROM_EMAIL')
        recipient_list = ['james@jamesflores.net']

        async_task(send_mail, subject, message, from_email, recipient_list)

        self.stdout.write(self.style.SUCCESS('Email sent successfully.'))
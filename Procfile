release: python manage.py migrate --noinput
web: gunicorn project.wsgi --log-file -
worker: python manage.py qcluster
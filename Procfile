web: gunicorn lancerpulse.wsgi:application --log-file -
release: python manage.py migrate && python manage.py seed_data

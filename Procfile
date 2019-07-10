release: python app.py db init
release: python app.py db upgrade
release: pip uninstall docker-pycreds
release: pip uninstall docker-py
web: gunicorn app:app
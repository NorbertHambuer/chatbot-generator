FROM python:alpine3.7

COPY . /app
WORKDIR /app

RUN mkdir -p /srv/config
ADD mode.conf /srv/config

RUN pip install -r requirements.txt

CMD python ./app.py
FROM python:alpine3.7

COPY . /app
WORKDIR /app


RUN apt-get -y install libc-dev
RUN apt-get -y install build-essential
RUN pip install -r requirements.txt

CMD python ./app.py
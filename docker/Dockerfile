FROM python:3.8-slim-buster

RUN apt update
RUN apt install -y python3 python3-venv python3-pip \
    npm \
    imagemagick \
    redis-server \
    git \
    gettext

RUN mkdir -p /var/prologin/gccsite

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt


WORKDIR /var/prologin/gccsite

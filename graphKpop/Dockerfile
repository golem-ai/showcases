FROM python:3.12.0a4-bullseye

RUN apt-get update
RUN apt-get upgrade -y

ENV PYTHONPATH=$PYTHONPATH:/demo:/demo/src

RUN pip3 install -U pip
RUN mkdir demo
COPY ./requirements.txt /demo/
RUN pip3 install -r /demo/requirements.txt

COPY ./ /demo

WORKDIR /demo

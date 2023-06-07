FROM python:3.12.0a4-bullseye

RUN apt-get update
RUN apt-get upgrade -y

ENV PYTHONPATH=$PYTHONPATH:/showcase:/showcase/src

RUN pip3 install -U pip
RUN mkdir showcase
COPY ./requirements.txt /showcase/
RUN pip3 install -r /showcase/requirements.txt

COPY ./ /showcase

WORKDIR /showcase

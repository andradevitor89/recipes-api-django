FROM python:3.9-alpine3.13
LABEL maintainer = "alvesvitor89"

ENV PYTHONUNBUFFERED 1
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./.dockerinit.sh /tmp/.dockerinit.sh
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false

RUN chmod +x /tmp/.dockerinit.sh && /tmp/.dockerinit.sh

ENV PATH="/py/bin:$PATH"

USER django-user
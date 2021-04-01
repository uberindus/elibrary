# pull official base image
FROM python:3.8.5-alpine

ENV APP_HOME /usr/src/app

# set work directory
WORKDIR $APP_HOME

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# install psycopg2 dependencies
RUN apk update \
    && apk add python3-dev musl-dev mariadb-dev gcc mysql-client

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt


# copy entrypoint.sh
COPY ./entrypoint.sh .

# copy project
COPY . .

# add custom parsing classes to the python search path 
ENV PYTHONPATH $APP_HOME/parsing

ENV JOURNALS_ROOT $APP_HOME/parsing/journals
ENV REPORTS_ROOT $APP_HOME/parsing/reports
ENV DUMPS_ROOT $APP_HOME/parsing/dumps

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
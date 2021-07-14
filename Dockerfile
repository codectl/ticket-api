FROM python:3.8

# set the current working directory
ARG CWD=/usr/local/app
RUN mkdir $CWD
WORKDIR $CWD

# proxy settings
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV http_proxy $HTTP_PROXY
ENV https_proxy $HTTPS_PROXY
ENV no_proxy $NO_PROXY

# set some environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY src/ src/

# get configurations
COPY .env .
COPY .flaskenv .

# run process as non root
USER 1000:1000

# command to run on container start
CMD [ "flask", "run" ]

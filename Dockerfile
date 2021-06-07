FROM python:3.8

# set the current working directory
ARG CWD /usr/local/app
RUN mkdir $CWD
WORKDIR $CWD

# install python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY src/ .

# and its files
COPY .env .
COPY .flaskenv .

# command to run on container start
CMD [ "flask", "run" ]

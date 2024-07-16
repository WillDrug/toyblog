FROM python:3.10

LABEL MAINTAINER="WillDrug"

# Create app directory
WORKDIR /app

COPY ./toycommons/requirements.txt ./
RUN pip install -r requirements.txt

# Install app dependencies
COPY ./requirements.txt ./
RUN pip install -r requirements.txt

# Bundle app source
COPY blog ./
COPY blog_web ./
COPY crawler ./
COPY toycommons ./
COPY main.py ./

CMD ["gunicorn", "-w",  "4", "-b", "0.0.0.0:80", "main:app"]
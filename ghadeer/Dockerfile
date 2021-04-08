FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /flaskapp
WORKDIR /flaskapp
RUN pip install --upgrade pip
COPY requirements.txt /flaskapp
RUN pip install -r requirements.txt
RUN python -m nltk.downloader popular
COPY . /flaskapp/

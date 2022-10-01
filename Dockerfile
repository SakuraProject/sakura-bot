FROM python:3

WORKDIR /usr/src/app

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y ffmpeg cmake gcc open_jtalk

RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install

COPY . /usr/src/app

CMD ["pipenv", "run", "python3", "main.py"]

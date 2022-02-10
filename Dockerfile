FROM python:3.9
WORKDIR /DigitalPower_test
COPY requirements.txt .
RUN pip3 install --upgrade pip -r requirements.txt
COPY ./docker/ /DigitalPower_test/docker
COPY ./src /DigitalPower_test/src
COPY ./setup.cfg/ /DigitalPower_test/setup.cfg
COPY ./.env /DigitalPower_test/.env
EXPOSE 8000
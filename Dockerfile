# syntax=docker/dockerfile:1.4
FROM python:3.10

WORKDIR /earthquake

COPY requirements.txt /earthquake
RUN pip3 install -r requirements.txt

COPY . /earthquake
EXPOSE 8050
ENTRYPOINT ["python3"]
CMD ["dash_earth.py"]
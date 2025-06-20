# Use the official Python image as a parent image
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
RUN apt-get -q update && apt-get -qy install netcat-traditional binutils libproj-dev gdal-bin ghostscript
RUN useradd -m app
RUN mkdir /app 
RUN chown app:app -R /app/
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
COPY . ./
USER app
EXPOSE 8000

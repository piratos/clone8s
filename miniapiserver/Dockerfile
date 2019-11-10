FROM ubuntu:18.04
RUN apt update && apt install -y python3-pip
COPY . /app
RUN pip3 install -r /app/requirements.txt
WORKDIR /app
EXPOSE 8080
ENTRYPOINT ["python3", "main.py"]


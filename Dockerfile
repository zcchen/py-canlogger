FROM debian:buster
RUN apt update \
    && apt upgrade -y \
    && apt install -yf \
        can-utils python3 python3-pip \
    && apt clean

RUN pip3 install --no-cache-dir canopen

ADD ./canlogger.py /canlogger.py

VOLUME /canlog

ENTRYPOINT ["python3", "/canlogger.py"]

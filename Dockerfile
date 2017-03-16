FROM python:2.7

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -qq -y --no-install-recommends \
    libbz2-dev \
    liblzma-dev \
    libmagic1 \
    libmuparser-dev \
    libsnappy-dev \
    libsparsehash-dev \
    python-ptrace \
    python-pygments \
    unzip \
    zip && apt-get clean && rm -rf /var/lib/apt/lists/*

# python requirements
ADD ./requirements.txt /tmp/requirements.txt
RUN cd /tmp/ && pip install -r requirements.txt

VOLUME /data
WORKDIR /opt/androguard
ADD . /opt/androguard

RUN python setup.py install

ENV PYTHON /usr/local/bin/python2.7
CMD ["androlyze.py", "-s"]

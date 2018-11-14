FROM nsqio/nsq
MAINTAINER Claudio Mastrapasqua <claudio.mastrapasqua@gmail.com>
COPY docker-entrypoint.sh nsq-ctrl.py /usr/local/bin/
RUN apk add --no-cache bind-tools python3 && pip3 install --upgrade pip requests dnspython
ENTRYPOINT ["docker-entrypoint.sh"]

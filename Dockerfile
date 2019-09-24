FROM python:3.7-alpine

RUN pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    pip install requests beautifulsoup4

COPY ./guraburu_news_delivery.py /var/docker_dir/guraburu_news_delivery.py
COPY ./config.ini /var/docker_dir/config.ini

RUN apk update && \
    apk --no-cache add tzdata && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    apk del tzdata

# 初期データを作成するために実行
RUN python /var/docker_dir/guraburu_news_delivery.py -r

# crontで定期実行
RUN echo '*/5 * * * * root python3 /var/docker_dir/guraburu_news_delivery.py' >> /var/spool/cron/crontabs/root
CMD crond -l 2 -f
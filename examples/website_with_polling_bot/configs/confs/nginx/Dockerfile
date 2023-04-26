FROM openresty/openresty:latest

COPY nginx.conf /etc/openresty/nginx.conf
COPY dj.conf /etc/nginx/conf.d/dj.conf
RUN rm /etc/nginx/conf.d/default.conf

ENV TZ=Europe/Moscow

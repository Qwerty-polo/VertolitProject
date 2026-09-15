FROM nginx:alpine


COPY nginx.conf \
    /etc/nginx/conf.d/default.conf


COPY index.html \
    booking.html \
    admin.html \
    /usr/share/nginx/html/


COPY css \
    /usr/share/nginx/html/css


COPY js \
    /usr/share/nginx/html/js


COPY assets \
    /usr/share/nginx/html/assets


EXPOSE 80
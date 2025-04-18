# Stage 1 removed — we don't need to build anything

FROM nginx:alpine

# Custom Nginx config (optional)
COPY nginx.conf /etc/nginx/nginx.conf

# Just copy the static HTML/CSS/JS
COPY . /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

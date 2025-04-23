# Stage 1 removed — we don't need to build anything

FROM nginx:alpine

# Custom Nginx config (optional)
COPY nginx.conf /etc/nginx/nginx.conf


ARG SET_BASE_URL=http://localhost:3000
ENV SET_BASE_URL=$SET_BASE_URL

COPY . /usr/share/nginx/html

# Inject SET_BASE_URL into config.js from config.template.js
RUN envsubst '${SET_BASE_URL}' < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js


EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

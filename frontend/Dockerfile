# Final version: serve static frontend only

FROM nginx:alpine

# Optional: custom Nginx config
COPY nginx.conf /etc/nginx/nginx.conf


ARG SET_BASE_URL=http://localhost:3000
ENV SET_BASE_URL=$SET_BASE_URL

COPY . /usr/share/nginx/html

# Inject SET_BASE_URL into config.js from config.template.js
RUN envsubst '${SET_BASE_URL}' < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js
RUN echo "SET_BASE_URL is: $SET_BASE_URL"


EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

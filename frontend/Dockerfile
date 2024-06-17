# Use an official Nginx image as a parent image
FROM nginx:alpine

# Copy static files to the Nginx html directory
COPY . /usr/share/nginx/html

# Copy Nginx configuration file
COPY nginx.conf /etc/nginx/nginx.conf

ENV SET_BASE_URL="http://localhost:3000"

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
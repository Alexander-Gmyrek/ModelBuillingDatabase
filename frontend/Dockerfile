# Stage 1: Build the frontend (assuming React, Vue, etc.)
FROM node:16 AS builder

WORKDIR /app
COPY . .

# Inject environment variable for backend API
ARG SET_BASE_URL=http://localhost:3000
ENV REACT_APP_BACKEND_URL=$SET_BASE_URL

RUN npm install && npm run build

# Stage 2: Serve the built app using Nginx
FROM nginx:alpine

# Replace default nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy only the build output
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

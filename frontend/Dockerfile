# Stage 1: Build the frontend
FROM node:16 AS builder

WORKDIR /app

# Copy and install only deps first (for caching)
COPY package*.json ./
RUN npm install

# Copy the rest of the app
COPY . .

# Inject backend base URL
ARG SET_BASE_URL=http://localhost:3000
ENV REACT_APP_BACKEND_URL=$SET_BASE_URL

# Build the app
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Use custom nginx config if needed
COPY nginx.conf /etc/nginx/nginx.conf

# Serve the built frontend
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

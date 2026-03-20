# Frontend Dockerfile for Vite React App
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server with host 0.0.0.0 to be accessible from outside container
CMD ["sh", "-c", "npm install && npx vite --host 0.0.0.0"]

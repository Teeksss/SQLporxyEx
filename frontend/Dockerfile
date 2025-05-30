FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    curl \
    wget \
    ca-certificates

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Clear npm cache and install dependencies
RUN npm cache clean --force
RUN npm install --silent --no-optional

# Copy source code
COPY . .

# Create build directory
RUN mkdir -p build

# Set permissions
RUN chown -R node:node /app
USER node

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["npm", "start"]
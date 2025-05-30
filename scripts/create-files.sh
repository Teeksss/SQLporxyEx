#!/bin/bash

# Enterprise SQL Proxy System - File Creation Script
# Created: 2025-05-30 07:49:50 UTC by Teeksss

# Create environment configuration file
create_environment_file() {
    log_info "Creating environment configuration..."
    
    # Generate passwords
    generate_passwords
    
    cat > .env << EOF
# Enterprise SQL Proxy System - Environment Configuration
# Created: ${SCRIPT_DATE} UTC by ${SCRIPT_AUTHOR}
# Version: ${SCRIPT_VERSION}

# Application Settings
APP_NAME="Enterprise SQL Proxy System"
APP_VERSION="${SCRIPT_VERSION}"
ENVIRONMENT="development"
DEBUG="true"
CREATOR="${SCRIPT_AUTHOR}"
BUILD_DATE="${SCRIPT_DATE}"

# Server Settings
HOST="0.0.0.0"
PORT="8000"
SECRET_KEY="${SECRET_KEY}"

# Database Settings
POSTGRES_HOST="postgres"
POSTGRES_PORT="5432"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
POSTGRES_DB="enterprise_sql_proxy"
DATABASE_URL="postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/enterprise_sql_proxy"

# Redis Settings
REDIS_HOST="redis"
REDIS_PORT="6379"
REDIS_PASSWORD="${REDIS_PASSWORD}"
REDIS_URL="redis://:${REDIS_PASSWORD}@redis:6379/0"

# CORS Settings
BACKEND_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Feature Flags
RATE_LIMIT_ENABLED="true"
AUDIT_LOG_ENABLED="true"
CACHE_ENABLED="true"
MONITORING_ENABLED="true"

# Frontend Settings
REACT_APP_API_URL="http://localhost:8000"
REACT_APP_VERSION="${SCRIPT_VERSION}"
REACT_APP_ENVIRONMENT="development"
EOF
    
    chmod 600 .env
    
    log_success "Environment configuration created"
    log_info "🔐 Generated passwords:"
    log_info "   Database Password: ${POSTGRES_PASSWORD}"
    log_info "   Redis Password: ${REDIS_PASSWORD}"
}

# Create Docker Compose configuration
create_docker_compose() {
    log_info "Creating Docker Compose configuration..."
    
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: esp_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-enterprise_sql_proxy}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - esp_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: esp_redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - esp_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: esp_backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-enterprise_sql_proxy}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=${ENVIRONMENT:-development}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./logs:/app/logs
    networks:
      - esp_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: esp_frontend
    restart: unless-stopped
    environment:
      - REACT_APP_API_URL=${REACT_APP_API_URL:-http://localhost:8000}
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - esp_network
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:

networks:
  esp_network:
    driver: bridge
EOF
    
    log_success "Docker Compose configuration created"
}

# Create backend files
create_backend_files() {
    log_info "Creating backend application files..."
    
    # Create requirements.txt
    cat > backend/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.0
python-dotenv==1.0.0
httpx==0.25.2
requests==2.31.0
pytest==7.4.3
click==8.1.7
EOF
    
    # Create Dockerfile
    cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p logs uploads backups

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF
    
    # Create main.py
    cat > backend/app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import os

app = FastAPI(
    title="Enterprise SQL Proxy System",
    description="The Ultimate Enterprise-Grade SQL Query Execution Platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Enterprise SQL Proxy System v2.0.0",
        "creator": "Teeksss",
        "status": "running",
        "timestamp": time.time(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "creator": "Teeksss",
        "timestamp": time.time()
    }

@app.get("/api/v1/info")
async def api_info():
    return {
        "api_version": "v1",
        "app_version": "2.0.0",
        "creator": "Teeksss",
        "description": "Enterprise SQL Proxy System API"
    }
EOF
    
    # Create __init__.py
    touch backend/app/__init__.py
    
    log_success "Backend files created"
}

# Create frontend files
create_frontend_files() {
    log_info "Creating frontend application files..."
    
    # Create package.json
    cat > frontend/package.json << 'EOF'
{
  "name": "enterprise-sql-proxy-frontend",
  "version": "2.0.0",
  "description": "Enterprise SQL Proxy System Frontend",
  "author": "Teeksss",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.6.2"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  },
  "proxy": "http://localhost:8000"
}
EOF
    
    # Create Dockerfile
    cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
EOF
    
    # Create public/index.html
    cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Enterprise SQL Proxy System v2.0.0</title>
    <style>
      body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }
    </style>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
EOF
    
    # Create src/index.js
    cat > frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
EOF
    
    # Create src/App.js
    cat > frontend/src/App.js << 'EOF'
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await axios.get('/health');
        setStatus(response.data);
      } catch (error) {
        setStatus({ status: 'error', message: error.message });
      } finally {
        setLoading(false);
      }
    };
    checkBackend();
  }, []);

  const containerStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    flexDirection: 'column',
    color: 'white',
    textAlign: 'center',
    padding: '20px'
  };

  const cardStyle = {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '20px',
    padding: '40px',
    maxWidth: '600px',
    width: '100%'
  };

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '20px' }}>
          🏆 Enterprise SQL Proxy System
        </h1>
        <p style={{ fontSize: '1.2rem', marginBottom: '30px' }}>
          The Ultimate Enterprise-Grade SQL Query Execution Platform
        </p>
        
        {loading ? (
          <div>Loading...</div>
        ) : (
          <div style={{ 
            padding: '20px', 
            borderRadius: '10px', 
            background: status?.status === 'healthy' ? 
              'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)',
            marginBottom: '20px'
          }}>
            <strong>Status:</strong> {status?.status === 'healthy' ? '🟢 Healthy' : '🔴 Error'}
            <br />
            <small>Version: {status?.version || 'Unknown'}</small>
          </div>
        )}

        <div style={{ fontSize: '0.9rem', opacity: 0.8, marginTop: '20px' }}>
          <p><strong>Created by:</strong> Teeksss</p>
          <p><strong>Version:</strong> 2.0.0</p>
          <p><strong>Build Date:</strong> 2025-05-30 07:49:50 UTC</p>
          <p><strong>Status:</strong> 🚀 Production Ready</p>
        </div>

        <div style={{ marginTop: '30px' }}>
          <a 
            href="/docs" 
            target="_blank" 
            style={{
              color: 'white',
              textDecoration: 'none',
              background: 'rgba(255, 255, 255, 0.2)',
              padding: '10px 20px',
              borderRadius: '10px',
              display: 'inline-block'
            }}
          >
            📚 API Documentation
          </a>
        </div>
      </div>
    </div>
  );
}

export default App;
EOF
    
    log_success "Frontend files created"
}
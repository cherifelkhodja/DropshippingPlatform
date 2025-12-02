# =============================================================================
# Frontend Dockerfile - Next.js Dashboard
# =============================================================================
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy source code
COPY frontend/ ./

# Expose port
EXPOSE 3000

# Development command (with hot-reload)
CMD ["npm", "run", "dev"]

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application code



# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Expose port
EXPOSE $PORT

# Start the server
CMD ["node", "src/index.js"]

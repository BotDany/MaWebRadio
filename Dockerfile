# Use Node.js base image
FROM node:20-alpine

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node dependencies
RUN npm ci

# Copy Python requirements
COPY requirements.txt ./

# Install Python dependencies using virtualenv to avoid externally-managed-environment
RUN python3 -m venv /app/venv
RUN . /app/venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port
EXPOSE 3000

# Start the app
CMD ["npm", "start"]

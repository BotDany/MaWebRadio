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

# Install Python dependencies
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port
EXPOSE 3000

# Start the app
CMD ["npm", "start"]

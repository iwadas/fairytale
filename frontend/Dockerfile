# Use an official Node image
FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the app code
COPY . .

# Expose the port (5173 is default for Vite, 8080 for Vue CLI)
EXPOSE 8080

# Start the app
# We use "-- --host" to tell Vite to listen on all network interfaces, not just localhost
CMD ["npm", "run", "serve", "--", "--port", "8080", "--host", "0.0.0.0"]
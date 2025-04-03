FROM node:18-alpine

WORKDIR /app

# Install curl for health checks
RUN apk --no-cache add curl wget

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all files
COPY . .

# Install PostCSS, Autoprefixer, and Tailwind CSS
RUN npm install -D tailwindcss postcss autoprefixer
RUN npx tailwindcss init -p

# Set environment variables for React
ENV NODE_ENV=production
ENV REACT_APP_API_URL=http://localhost:8000

# Build the app for production
RUN npm run build

# Install serve to run the build
RUN npm install -g serve

# Expose port 3000
EXPOSE 3000

# Start the app with proper serve syntax
# The error was in the `--listen` parameter format
CMD ["serve", "-s", "build", "-l", "3000"]
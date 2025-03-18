# Dockerfile for Frontend
FROM nginx:alpine

# Copy the HTML files to the Nginx server
COPY src /usr/share/nginx/html

# Expose the port the app runs on
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"] 
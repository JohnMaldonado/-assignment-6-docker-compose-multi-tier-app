# Stage 1: Build stage - Simple static HTML
FROM node:18-alpine AS builder

WORKDIR /app

# Copy all source files
COPY public/ ./public/
COPY src/ ./src/

# Create build directory with static files
RUN mkdir -p build && \
    cp -r public/* build/ && \
    cp -r src/* build/

# Stage 2: Production stage with Nginx
FROM nginx:1.25-alpine

# Create non-root user for security
RUN addgroup -g 1000 jhonapp && \
    adduser -D -u 1000 -G jhonapp jhonapp

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static files from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Change ownership of nginx files to non-root user
RUN chown -R jhonapp:jhonapp /usr/share/nginx/html && \
    chown -R jhonapp:jhonapp /var/cache/nginx && \
    chown -R jhonapp:jhonapp /var/log/nginx && \
    chown -R jhonapp:jhonapp /etc/nginx/conf.d

# Create PID file directory with correct permissions
RUN touch /var/run/nginx.pid && \
    chown -R jhonapp:jhonapp /var/run/nginx.pid

# Switch to non-root user
USER jhonapp

# Expose port
EXPOSE 3000

# Health check to verify Nginx is serving files
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Start Nginx in foreground mode (SIN comillas JSON)
CMD nginx -g 'daemon off;'

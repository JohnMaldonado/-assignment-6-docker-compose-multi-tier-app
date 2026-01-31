FROM nginx:1.25-alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

RUN addgroup -g 1000 jhonapp && \
    adduser -D -u 1000 -G jhonapp jhonapp

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/

RUN mkdir -p /var/cache/nginx /var/log/nginx && \
    chown -R jhonapp:jhonapp /var/cache/nginx && \
    chown -R jhonapp:jhonapp /var/log/nginx && \
    chown -R jhonapp:jhonapp /etc/nginx

RUN touch /var/run/nginx.pid && \
    chown -R jhonapp:jhonapp /var/run/nginx.pid

USER jhonapp

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

CMD nginx -g 'daemon off;'

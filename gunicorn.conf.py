# Gunicorn configuration for production deployment
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync" 
worker_connections = 1000
timeout = 120
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

### File: nginx.conf

```nginx
# Nginx configuration for MyAIGist
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/myaigist/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
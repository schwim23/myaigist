# Gunicorn configuration for production deployment
bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 120
max_requests = 1000
max_requests_jitter = 50
preload_app = True

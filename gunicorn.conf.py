import multiprocessing

# Render recommends 1-2 workers for free tier (512MB RAM)
# WEB_CONCURRENCY env var sets this, but default fallback is safe.
workers = 2 

# Threads per worker
threads = 2

# Timeout: Increase from default 30s to 60s to handle slow DB/cold starts
timeout = 60

# Logging: Output to stdout (seen in Render logs)
accesslog = '-'
errorlog = '-'

# Forwarded headers (critical for HTTPS on Render)
forwarded_allow_ips = '*'

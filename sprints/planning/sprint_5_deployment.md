# Sprint 5: Deployment & Operations

**Duration:** 1 week  
**Status:** Planning  
**Depends On:** Sprint 4 completion  
**Deployment Target:** Docker  

---

## Goal

Production deployment ready with Docker containerization

## Deliverables

- [ ] Docker containerization
- [ ] docker-compose for local dev
- [ ] Health check endpoints
- [ ] Logging aggregation
- [ ] Error alerting
- [ ] Backup/restore procedures
- [ ] Runbook documentation

## Success Metrics

- One-command deployment
- Automated health monitoring
- <5 min recovery time from failures

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Install application
RUN pip install -e .

# Create data directory
RUN mkdir -p /app/data /app/logs

# Environment variables
ENV PITCHBOOK_DB_PATH=/app/data/ai_news.db
ENV PITCHBOOK_LOG_FILE=/app/logs/pitchbook.log

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose API port
EXPOSE 8000

# Default command
CMD ["pitchbook", "serve", "--host", "0.0.0.0"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  pitchbook:
    build: .
    container_name: pitchbook-api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PITCHBOOK_API_HOST=0.0.0.0
      - PITCHBOOK_API_PORT=8000
      - PITCHBOOK_LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  scheduler:
    build: .
    container_name: pitchbook-scheduler
    command: pitchbook schedule start
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PITCHBOOK_SCRAPE_HOUR=2
      - PITCHBOOK_SCRAPE_MINUTE=0
    depends_on:
      - pitchbook
    restart: unless-stopped

volumes:
  data:
  logs:
```

### .dockerignore

```
.git
.venv
__pycache__
*.pyc
*.pyo
.pytest_cache
.coverage
*.egg-info
.env
tests/
docs/
*.md
```

## Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Health check for container orchestration."""
    db_ok = check_database_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "checks": {
            "database": "ok" if db_ok else "error"
        }
    }
```

## Backup Strategy

```bash
# Automated daily backup
pitchbook db export --output /backups/ai_news_$(date +%Y%m%d).json

# Restore from backup
pitchbook db import --input /backups/ai_news_20260219.json
```

## Operations Runbook

### Startup

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f pitchbook
```

### Manual Scrape

```bash
docker-compose exec pitchbook pitchbook scrape --source all
```

### Database Backup

```bash
docker-compose exec pitchbook pitchbook db export --output /app/data/backup.json
```

---

## Tasks Breakdown

*To be detailed when sprint becomes active*

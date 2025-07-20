# LogBERT AI Agents - Docker Deployment Guide
## 🐳 Complete Containerization Solution

This directory contains all the necessary files to run the LogBERT AI Agents system using Docker and Docker Compose.

## 📋 Prerequisites

- Docker Engine 20.10+ 
- Docker Compose 2.0+
- At least 4GB of available RAM
- 10GB of free disk space

## 🚀 Quick Start

### Production Deployment

```bash
# Build and start all services
./docker-scripts.sh build
./docker-scripts.sh start

# Or using docker-compose directly
docker-compose up -d
```

### Development Mode

```bash
# Start development services with hot reloading
./docker-scripts.sh dev

# Or using docker-compose directly
docker-compose -f docker-compose.dev.yml up -d
```

## 📁 Docker Files Overview

### Core Files
- **`Dockerfile`** - Multi-stage build configuration
- **`docker-compose.yml`** - Production orchestration
- **`docker-compose.dev.yml`** - Development setup
- **`.dockerignore`** - Build optimization
- **`docker-scripts.sh`** - Management utilities

### Services Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   LogBERT API   │    │      Redis      │
│   Port: 8000    │◄──►│   Port: 6379    │
└─────────────────┘    └─────────────────┘
          │                        
          ▼                        
┌─────────────────┐                
│   Frontend      │                
│  (if enabled)   │                
└─────────────────┘
```

## 🛠️ Management Commands

### Using the Management Script

```bash
# Build Docker images
./docker-scripts.sh build

# Start production services
./docker-scripts.sh start

# Start development services
./docker-scripts.sh dev

# View logs
./docker-scripts.sh logs
./docker-scripts.sh logs logbert-api

# Run tests
./docker-scripts.sh test

# Stop all services
./docker-scripts.sh stop

# Clean up resources
./docker-scripts.sh cleanup
```

### Direct Docker Commands

```bash
# Build production image
docker build --target production -t logbert-hadoop-rca:latest .

# Build development image
docker build --target development --build-arg INSTALL_DEV=true -t logbert-hadoop-rca:dev .

# Run single container
docker run -p 8000:8000 logbert-hadoop-rca:latest

# View container logs
docker logs logbert-api

# Execute commands in container
docker exec -it logbert-api bash
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGBERT_ENV` | `production` | Environment mode |
| `LOGBERT_LOG_LEVEL` | `INFO` | Logging level |
| `LOGBERT_HOST` | `0.0.0.0` | Bind host |
| `LOGBERT_PORT` | `8000` | Service port |
| `LOGBERT_WORKERS` | `4` | Worker processes |

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./logs` | `/app/logs` | Log persistence |
| `./uploads` | `/app/uploads` | File uploads |
| `./AI_MODELS` | `/app/AI_MODELS` | Model storage |

## 📊 Monitoring

### Health Checks

The API includes built-in health checks:

```bash
# Check API health
curl http://localhost:8000/health

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 🔒 Security Features

- Non-root user execution
- Multi-stage builds for minimal attack surface
- Resource limits and constraints
- Health checks for monitoring
- Secure defaults for production

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
sudo lsof -i :8000

# Stop conflicting services
./docker-scripts.sh stop
```

**Out of Memory**
```bash
# Check Docker resources
docker system df
docker stats

# Clean up unused resources
./docker-scripts.sh cleanup
```

**Build Failures**
```bash
# Clean build cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Debug Mode

```bash
# Run container in interactive mode
docker run -it --rm logbert-hadoop-rca:dev bash

# Check container logs
docker logs -f logbert-api

# Monitor resource usage
docker stats logbert-api
```

## 📈 Performance Optimization

### Production Tuning

1. **Adjust worker processes** based on CPU cores:
   ```yaml
   environment:
     - LOGBERT_WORKERS=8  # 2x CPU cores
   ```

2. **Configure resource limits**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '4.0'
         memory: 8G
   ```

3. **Use external volumes** for large datasets:
   ```yaml
   volumes:
     - /data/models:/app/AI_MODELS
   ```

### Development Optimization

1. **Use volume mounts** for faster development:
   ```yaml
   volumes:
     - .:/app
   ```

2. **Enable hot reloading**:
   ```bash
   ./docker-scripts.sh dev
   ```

## 🌐 Production Deployment

### Recommended Setup

1. **Use a reverse proxy** (nginx/traefik)
2. **Configure SSL/TLS** certificates
3. **Set up log aggregation** (ELK stack)
4. **Regular backups** of volumes

### Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/)

## 🤝 Contributing

When contributing Docker-related changes:

1. Test both production and development builds
2. Update documentation for new features
3. Ensure security best practices
4. Test resource limits and performance

---

**Happy Containerizing! 🐳**

# 🐛 Troubleshooting Guide

Common issues and solutions for the Docker Compose application.

---

## 📋 Table of Contents

1. [Services Not Starting](#services-not-starting)
2. [Port Conflicts](#port-conflicts)
3. [Database Issues](#database-issues)
4. [Network Problems](#network-problems)
5. [Performance Issues](#performance-issues)
6. [Build Failures](#build-failures)

---

## 🚨 Services Not Starting

### Symptom: Container exits immediately
```bash
docker-compose ps
# Shows: jhon-backend    Exited (1)
```

**Diagnosis:**
```bash
# Check logs
docker-compose logs jhon-backend

# Common errors:
# - "connection refused" → Database not ready
# - "ModuleNotFoundError" → Build issue
# - "Permission denied" → File permissions
```

**Solutions:**
```bash
# Solution 1: Wait for dependencies
docker-compose down
docker-compose up -d
# Health checks will ensure proper startup order

# Solution 2: Rebuild images
docker-compose build --no-cache jhon-backend
docker-compose up -d

# Solution 3: Check environment variables
cat .env
# Ensure all required variables are set
```

---

### Symptom: Service stuck in "starting" state
```bash
docker-compose ps
# Shows: jhon-backend    Up (starting)
```

**Diagnosis:**
```bash
# Check health check status
docker inspect jhon-backend --format='{{json .State.Health}}' | ConvertFrom-Json

# Check logs for errors
docker-compose logs jhon-backend --tail=50
```

**Solutions:**
```bash
# Solution 1: Increase start_period in health check
# Edit docker-compose.yml:
healthcheck:
  start_period: 40s  # Increase from 5s

# Solution 2: Fix health check command
# Ensure curl/wget is installed in container

# Solution 3: Remove health check temporarily
# Comment out healthcheck section to isolate issue
```

---

## 🔌 Port Conflicts

### Symptom: "port is already allocated"
```bash
docker-compose up -d
# Error: Bind for 0.0.0.0:80 failed: port is already allocated
```

**Diagnosis:**
```bash
# Windows: Find process using port
netstat -ano | findstr :80

# Output example:
# TCP    0.0.0.0:80    0.0.0.0:0    LISTENING    12345
#                                                  ^^^^^ PID
```

**Solutions:**
```bash
# Solution 1: Kill the process
Stop-Process -Id 12345 -Force

# Solution 2: Change port in docker-compose.yml
services:
  jhon-nginx:
    ports:
      - "8080:80"  # Use 8080 instead of 80

# Solution 3: Stop other Docker containers
docker ps
docker stop <container-using-port-80>
```

---

## 💾 Database Issues

### Symptom: "Connection refused" to PostgreSQL
```bash
# Backend logs show:
# psycopg2.OperationalError: could not connect to server
```

**Diagnosis:**
```bash
# Check if PostgreSQL is running
docker-compose ps jhon-postgres

# Check PostgreSQL health
docker-compose exec jhon-postgres pg_isready -U jhon_user
```

**Solutions:**
```bash
# Solution 1: Wait for PostgreSQL to be ready
# Health checks should handle this automatically

# Solution 2: Verify environment variables
docker-compose exec jhon-backend env | grep DB_

# Should show:
# DB_HOST=jhon-postgres
# DB_NAME=jhon_db
# DB_USER=jhon_user
# DB_PASSWORD=***

# Solution 3: Reset database
docker-compose down -v  # WARNING: Deletes data
docker-compose up -d
curl -X POST http://localhost/api/init-db
```

---

### Symptom: "Authentication failed" for PostgreSQL
```bash
# Error: FATAL: password authentication failed for user "jhon_user"
```

**Solutions:**
```bash
# Solution 1: Check .env file
cat .env | grep DB_PASSWORD

# Solution 2: Ensure .env is loaded
docker-compose config | grep POSTGRES_PASSWORD

# Solution 3: Recreate containers with new password
docker-compose down -v
# Edit .env with new password
docker-compose up -d
```

---

### Symptom: Database data lost after restart
```bash
# All tasks disappear after docker-compose down
```

**Diagnosis:**
```bash
# Check if volume exists
docker volume ls | Select-String "jhon-postgres-data"

# Check if volume is mounted
docker inspect jhon-postgres --format='{{json .Mounts}}'
```

**Solutions:**
```bash
# Solution 1: Don't use -v flag
docker-compose down      # Good: keeps volumes
docker-compose down -v   # Bad: deletes volumes

# Solution 2: Verify volume configuration
# In docker-compose.yml, ensure:
volumes:
  jhon-postgres-data:
    name: jhon-postgres-data

services:
  jhon-postgres:
    volumes:
      - jhon-postgres-data:/var/lib/postgresql/data

# Solution 3: Restore from backup
docker exec -i jhon-postgres psql -U jhon_user jhon_db < backup.sql
```

---

## 🌐 Network Problems

### Symptom: "Could not resolve host" between containers
```bash
# Backend logs:
# redis.exceptions.ConnectionError: Error connecting to jhon-redis:6379
```

**Diagnosis:**
```bash
# Check if containers are on same network
docker network inspect jhon-backend-network

# Should show both jhon-backend and jhon-redis
```

**Solutions:**
```bash
# Solution 1: Recreate networks
docker-compose down
docker network prune
docker-compose up -d

# Solution 2: Verify network configuration
docker-compose config | grep -A 5 "networks:"

# Solution 3: Use IP instead of hostname (temporary)
# In .env:
REDIS_HOST=172.19.0.3  # Find IP with: docker inspect jhon-redis
```

---

### Symptom: Frontend can't reach Backend API
```bash
# Browser console:
# Failed to fetch: http://localhost/api/tasks
```

**Diagnosis:**
```bash
# Test backend directly
curl http://localhost:5000/api/tasks

# Test through nginx
curl http://localhost/api/tasks

# Check nginx logs
docker-compose logs jhon-nginx --tail=20
```

**Solutions:**
```bash
# Solution 1: Check nginx routing
docker-compose exec jhon-nginx cat /etc/nginx/conf.d/nginx.conf

# Should have:
# location /api {
#     proxy_pass http://jhon-backend:5000;
# }

# Solution 2: Verify backend is accessible from nginx
docker-compose exec jhon-nginx curl http://jhon-backend:5000/health

# Solution 3: Restart nginx
docker-compose restart jhon-nginx
```

---

## ⚡ Performance Issues

### Symptom: Slow response times
```bash
# API calls taking >1 second
```

**Diagnosis:**
```bash
# Check resource usage
docker stats

# Check if containers are hitting resource limits
docker inspect jhon-backend --format='{{json .HostConfig.Memory}}'

# Check Redis cache hit rate
docker-compose logs jhon-backend | Select-String "cache"
```

**Solutions:**
```bash
# Solution 1: Increase resource limits
# In docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '2.0'      # Increase from 1.0
      memory: 1024M    # Increase from 512M

# Solution 2: Verify Redis is caching
curl http://localhost/api/tasks  # First call (database)
curl http://localhost/api/tasks  # Second call (should be cache)

# Solution 3: Check database query performance
docker-compose exec jhon-postgres psql -U jhon_user jhon_db -c "EXPLAIN ANALYZE SELECT * FROM tasks"
```

---

### Symptom: High CPU usage
```bash
docker stats
# Shows: jhon-backend CPU: 95%
```

**Solutions:**
```bash
# Solution 1: Check for infinite loops
docker-compose logs jhon-backend --tail=100
# Look for repeated error messages

# Solution 2: Restart container
docker-compose restart jhon-backend

# Solution 3: Scale horizontally
docker-compose up --scale jhon-backend=3
```

---

## 🔨 Build Failures

### Symptom: "No such file or directory" during build
```bash
docker-compose build
# Error: COPY failed: file not found
```

**Solutions:**
```bash
# Solution 1: Check .dockerignore
cat backend/.dockerignore
# Ensure you're not ignoring required files

# Solution 2: Verify file exists
Get-ChildItem backend -Recurse

# Solution 3: Check Dockerfile COPY paths
# Ensure paths are relative to build context
```

---

### Symptom: "pip install" fails in backend build
```bash
# Error: Could not find a version that satisfies the requirement
```

**Solutions:**
```bash
# Solution 1: Update requirements.txt versions
# Replace == with >= for flexibility

# Solution 2: Build with --no-cache
docker-compose build --no-cache jhon-backend

# Solution 3: Check network during build
# Ensure Docker can reach PyPI
docker run --rm python:3.11-alpine pip install Flask
```

---

## 🔍 Diagnostic Commands

### Quick Health Check
```bash
# Check all services
docker-compose ps

# Check specific service health
docker inspect jhon-backend --format='{{.State.Health.Status}}'

# View all logs
docker-compose logs --tail=50

# Follow logs live
docker-compose logs -f jhon-backend
```

### Network Diagnostics
```bash
# List networks
docker network ls | Select-String "jhon"

# Inspect network
docker network inspect jhon-frontend-network

# Test connectivity between containers
docker-compose exec jhon-backend ping jhon-postgres
docker-compose exec jhon-backend curl jhon-redis:6379
```

### Volume Diagnostics
```bash
# List volumes
docker volume ls | Select-String "jhon"

# Inspect volume
docker volume inspect jhon-postgres-data

# Check volume contents
docker run --rm -v jhon-postgres-data:/data alpine ls -la /data
```

---

## 🆘 Nuclear Option: Complete Reset
```bash
# WARNING: This deletes ALL data

# Stop all containers
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Clean Docker system
docker system prune -a --volumes

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d

# Reinitialize database
curl -X POST http://localhost/api/init-db
```

---

## 📞 Getting Help

If you're still stuck:

1. **Check logs first:**
```bash
   docker-compose logs jhon-backend --tail=100 > logs.txt
```

2. **Verify configuration:**
```bash
   docker-compose config > config.txt
```

3. **Document your environment:**
```bash
   docker --version > environment.txt
   docker-compose --version >> environment.txt
   Get-ComputerInfo | Select-Object OsName, OsVersion >> environment.txt
```

4. **Create GitHub Issue** with logs, config, and environment info

---

[← Back to README](../README.md)

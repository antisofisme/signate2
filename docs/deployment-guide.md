# Anthias SaaS Platform - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Anthias SaaS Platform to production environments. The deployment uses Docker Compose with a multi-service architecture designed for high availability, security, and scalability.

## Architecture

### Services Overview

- **PostgreSQL Database**: Primary data storage with optimized configuration
- **Redis Cache**: Session storage, caching, and Celery message broker
- **Django Backend**: Main application server with API endpoints
- **WebSocket Service**: Real-time communication support
- **Celery Workers**: Background task processing
- **Celery Beat**: Scheduled task management
- **Next.js Frontend**: React-based user interface
- **Nginx**: Reverse proxy, load balancer, and SSL termination
- **Certbot**: Automated SSL certificate management
- **Monitoring**: System health and performance monitoring
- **Backup Service**: Automated data backup and recovery

### Network Architecture

```
Internet → Nginx (SSL/TLS) → Application Services
                          ↓
                    Backend Network (Isolated)
```

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04 LTS or newer, CentOS 8+, or similar Linux distribution
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Storage**: Minimum 100GB SSD, Recommended 500GB+ NVMe SSD
- **Network**: Static IP address, domain name configured

### Software Requirements

- Docker 24.0+ and Docker Compose 2.0+
- Git
- OpenSSL
- Curl
- Basic command line tools (bash, grep, awk, etc.)

### Domain and DNS Setup

1. Configure A records for your domain(s)
2. Ensure ports 80 and 443 are accessible
3. Configure proper SPF/DKIM records for email (optional)

## Installation Steps

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply docker group changes
```

### 2. Application Deployment

```bash
# Clone the repository
git clone <repository-url> /opt/signate
cd /opt/signate

# Create data directories
sudo mkdir -p data/{postgres,redis,anthias,static,media,backups,logs,ssl/{certs,private}}
sudo chown -R $USER:$USER data/

# Configure environment
cp .env.production.example .env.production
```

### 3. Environment Configuration

Edit `.env.production` with your specific values:

```bash
# Required Settings
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SERVER_NAME=yourdomain.com

# Database
POSTGRES_PASSWORD=secure-database-password
DATABASE_URL=postgresql://anthias:secure-database-password@postgres:5432/anthias_production

# Redis
REDIS_URL=redis://redis:6379/0

# SSL Configuration
SSL_DOMAINS=yourdomain.com,www.yourdomain.com
SSL_EMAIL=admin@yourdomain.com

# Frontend URLs
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXT_PUBLIC_WS_URL=wss://yourdomain.com/ws

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Notification URLs (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 4. SSL Certificate Setup

```bash
# Setup SSL certificates
./scripts/setup-ssl.sh -e admin@yourdomain.com -d "yourdomain.com,www.yourdomain.com"

# For staging environment, add --staging flag
./scripts/setup-ssl.sh --staging -e admin@yourdomain.com -d "staging.yourdomain.com"
```

### 5. Database Migration

```bash
# Run database migrations
./scripts/migrate-database.sh

# Create superuser account
docker-compose -f docker/docker-compose.production.yml --env-file .env.production exec anthias-server \
    python manage.py createsuperuser
```

### 6. Application Startup

```bash
# Start all services
docker-compose -f docker/docker-compose.production.yml --env-file .env.production up -d

# Verify deployment
./scripts/health-check.sh
```

## Configuration Management

### Environment Variables

Key environment variables for production:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `SSL_DOMAINS` | SSL certificate domains | Yes |
| `SSL_EMAIL` | Let's Encrypt email | Yes |

### Security Configuration

```bash
# Generate secure secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Configure firewall (UFW example)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Database Configuration

PostgreSQL is configured with:
- Connection pooling (25 connections, 15 overflow)
- Query optimization settings
- Automated backups
- SSL connections (optional)

### Caching Configuration

Redis is configured with:
- 1GB memory limit with LRU eviction
- Persistence enabled (RDB + AOF)
- Connection limits and timeouts
- Security hardening

## Monitoring and Health Checks

### Health Check Endpoints

- **Application Health**: `https://yourdomain.com/health`
- **API Health**: `https://yourdomain.com/api/v1/health`
- **Frontend Health**: `https://yourdomain.com/api/health`

### Automated Health Monitoring

```bash
# Run comprehensive health check
./scripts/health-check.sh

# Setup automated health monitoring (cron)
echo "*/5 * * * * /opt/signate/scripts/health-check.sh" | crontab -
```

### Log Management

Logs are stored in `/opt/signate/data/logs/`:
- `anthias.log` - Application logs
- `deployment.log` - Deployment logs
- `backup.log` - Backup operation logs
- `health-check.log` - Health check logs
- `ssl-renewal.log` - SSL renewal logs

### Performance Monitoring

Monitor key metrics:
- CPU and memory usage
- Database connection counts
- Redis memory usage
- Disk space utilization
- SSL certificate expiration

## Backup and Recovery

### Automated Backups

Backups run daily at 2 AM and include:
- Database dump (compressed)
- Media files
- Configuration files
- SSL certificates

```bash
# Manual backup
./scripts/backup-production.sh

# Restore from backup
./scripts/restore-backup.sh /path/to/backup/directory
```

### Backup Storage

- **Local**: `/opt/signate/data/backups/`
- **Cloud**: S3-compatible storage (optional)
- **Retention**: 30 days (configurable)

## Scaling and Load Balancing

### Horizontal Scaling

To scale the application:

1. **Database**: Use PostgreSQL clustering or read replicas
2. **Application**: Increase Docker Compose replica count
3. **Cache**: Use Redis Cluster for high availability
4. **Storage**: Use external object storage (S3, etc.)

### Load Balancing

Nginx is configured with:
- Upstream load balancing
- Health checks
- Session affinity (if needed)
- Rate limiting

Example scaling configuration:

```yaml
# In docker-compose.production.yml
anthias-server:
  deploy:
    replicas: 3

anthias-celery:
  deploy:
    replicas: 2
```

## Security Best Practices

### Application Security

- Regular security updates
- Strong password policies
- JWT token management
- CORS configuration
- SQL injection protection

### Infrastructure Security

- Firewall configuration
- SSL/TLS encryption
- Security headers
- Rate limiting
- Access logging

### Monitoring Security

```bash
# Check for security vulnerabilities
docker scan anthias-server:latest

# Monitor failed login attempts
grep "authentication failed" /opt/signate/data/logs/anthias.log

# Check SSL certificate status
./scripts/setup-ssl.sh --check
```

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check service status
docker-compose -f docker/docker-compose.production.yml ps

# Check logs
docker-compose -f docker/docker-compose.production.yml logs service-name

# Check system resources
df -h
free -h
```

#### Database Connection Issues

```bash
# Test database connectivity
docker-compose -f docker/docker-compose.production.yml exec postgres \
    pg_isready -U anthias -d anthias_production

# Check database logs
docker-compose -f docker/docker-compose.production.yml logs postgres
```

#### SSL Certificate Issues

```bash
# Check certificate status
openssl x509 -in /opt/signate/data/ssl/certs/fullchain.pem -text -noout

# Renew certificates manually
./scripts/setup-ssl.sh --renew

# Check Let's Encrypt rate limits
# https://letsencrypt.org/docs/rate-limits/
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Analyze slow queries
docker-compose -f docker/docker-compose.production.yml exec postgres \
    psql -U anthias -d anthias_production -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Check Redis memory usage
docker-compose -f docker/docker-compose.production.yml exec redis redis-cli info memory
```

### Debug Mode

For debugging in production (use carefully):

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services
docker-compose -f docker/docker-compose.production.yml restart
```

## Maintenance

### Regular Maintenance Tasks

1. **Daily**: Monitor health checks and logs
2. **Weekly**: Review security logs and performance metrics
3. **Monthly**: Update system packages and Docker images
4. **Quarterly**: Review and update SSL certificates, backup procedures

### Update Procedure

```bash
# Backup before update
./scripts/backup-production.sh

# Pull latest code
git pull origin main

# Update Docker images
docker-compose -f docker/docker-compose.production.yml pull

# Run migrations
./scripts/migrate-database.sh

# Restart services
docker-compose -f docker/docker-compose.production.yml up -d

# Verify deployment
./scripts/health-check.sh
```

### Rollback Procedure

```bash
# Rollback to previous version
git checkout previous-tag

# Restore database if needed
./scripts/restore-backup.sh /path/to/backup

# Restart services
docker-compose -f docker/docker-compose.production.yml up -d
```

## Support and Documentation

### Additional Resources

- **API Documentation**: `https://yourdomain.com/api/docs/`
- **Admin Interface**: `https://yourdomain.com/admin/`
- **Health Dashboard**: `https://yourdomain.com/health`

### Getting Help

1. Check application logs for error messages
2. Review this documentation for common solutions
3. Consult the project's issue tracker
4. Contact the development team

### Contributing

For deployment improvements and bug fixes:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed description

---

**Note**: This deployment guide assumes a single-server setup. For multi-server deployments, additional configuration for service discovery, shared storage, and database clustering may be required.
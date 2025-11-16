# Production Deployment Guide

This directory contains production-ready deployment configurations for the data warehouse orchestration system.

## Deployment Options

### 1. Script-Based (Recommended for Development/Small Production)

**Quick Start:**

```bash
# Start everything (server + worker)
./scripts/orchestration.sh start

# Check status
./scripts/orchestration.sh status

# View logs
./scripts/orchestration.sh logs server
./scripts/orchestration.sh logs worker-dev

# Stop everything
./scripts/orchestration.sh stop
```

**Features:**

- ✅ Single command to start/stop
- ✅ Background processes with PID tracking
- ✅ Centralized logging in `logs/` directory
- ✅ Status monitoring
- ✅ Automatic restart on failure (manual)

**Production Usage:**

```bash
# Start production environment
./scripts/orchestration.sh start prod

# Monitor production logs
./scripts/orchestration.sh logs worker-prod

# Restart production
./scripts/orchestration.sh restart prod
```

---

### 2. Systemd Services (Linux Production)

**Installation:**

```bash
# 1. Update paths in service files
cd deployment/systemd
sed -i 's|/path/to/data-warehouse|'"$(pwd)"'|g' *.service

# 2. Copy to systemd
sudo cp prefect-server.service /etc/systemd/system/
sudo cp prefect-worker@.service /etc/systemd/system/

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable services
sudo systemctl enable prefect-server
sudo systemctl enable prefect-worker@dev
sudo systemctl enable prefect-worker@prod

# 5. Start services
sudo systemctl start prefect-server
sudo systemctl start prefect-worker@dev
```

**Management:**

```bash
# Status
sudo systemctl status prefect-server
sudo systemctl status prefect-worker@dev

# Logs
sudo journalctl -u prefect-server -f
sudo journalctl -u prefect-worker@dev -f

# Restart
sudo systemctl restart prefect-server
sudo systemctl restart prefect-worker@prod
```

**Features:**

- ✅ Automatic startup on boot
- ✅ Automatic restart on failure
- ✅ Systemd logging (journald)
- ✅ User isolation
- ✅ Dependency management

---

### 3. Docker Compose (Cloud/Container Production)

**Quick Start:**

```bash
cd deployment/docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f prefect-worker-dev

# Stop all services
docker-compose down
```

**Features:**

- ✅ PostgreSQL database (persistent storage)
- ✅ Isolated network
- ✅ Volume management
- ✅ Easy scaling
- ✅ Cloud-ready

**Production Configuration:**

```bash
# Edit docker-compose.yml
# Uncomment prefect-worker-prod section

# Start with production worker
docker-compose up -d

# Scale workers
docker-compose up -d --scale prefect-worker-dev=3
```

**Database Persistence:**

```bash
# Backup database
docker-compose exec postgres pg_dump -U prefect prefect > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U prefect prefect
```

---

## Comparison

| Feature                | Script     | Systemd      | Docker Compose    |
| ---------------------- | ---------- | ------------ | ----------------- |
| **Setup Complexity**   | Easy       | Medium       | Medium            |
| **Auto-restart**       | Manual     | Yes          | Yes               |
| **Boot Startup**       | No         | Yes          | Yes (with config) |
| **Logging**            | File-based | Journald     | Docker logs       |
| **Resource Isolation** | No         | Partial      | Full              |
| **Database**           | SQLite     | SQLite       | PostgreSQL        |
| **Scaling**            | Manual     | Manual       | Easy              |
| **Cloud Ready**        | No         | Partial      | Yes               |
| **Best For**           | Dev/Small  | Linux Server | Cloud/Container   |

---

## Monitoring & Alerts

### Health Checks

Add to cron (script-based):

```bash
*/5 * * * * /path/to/data-warehouse/scripts/orchestration.sh status | grep "Not running" && /path/to/data-warehouse/scripts/orchestration.sh restart
```

### Metrics

All deployments expose:

- Flow run status at http://127.0.0.1:4200
- Logs in respective log files/streams
- System metrics via standard tools

### Alerting

Configure in Prefect UI:

- Navigate to Settings → Notifications
- Add Slack/Email webhooks
- Set conditions (failure, SLA miss, etc.)

---

## Production Checklist

- [ ] Choose deployment method (script/systemd/docker)
- [ ] Update all file paths in configs
- [ ] Set up PostgreSQL (docker) or use SQLite (script/systemd)
- [ ] Configure environment-specific triggers (prod/)
- [ ] Set up monitoring/alerting
- [ ] Test failover scenarios
- [ ] Document recovery procedures
- [ ] Set up backups (database, configs)
- [ ] Configure log rotation
- [ ] Set up firewall rules (port 4200)
- [ ] Configure secrets management (.env files)
- [ ] Test deployment in staging first

---

## Environments

### Development (`dev`)

```bash
./scripts/orchestration.sh start dev
```

- Frequent schedules for testing
- Lower retry attempts
- Debug logging

### Staging (`stage`)

```bash
./scripts/orchestration.sh start stage
```

- Production-like schedules
- Full retry logic
- Test alerts

### Production (`prod`)

```bash
./scripts/orchestration.sh start prod
```

- Real schedules
- Full monitoring
- Critical alerts

---

## Troubleshooting

### Server won't start

```bash
# Check logs
./scripts/orchestration.sh logs server

# Check port
lsof -i :4200

# Kill conflicting process
pkill -f "prefect server"
```

### Worker not executing flows

```bash
# Check worker logs
./scripts/orchestration.sh logs worker-dev

# Verify connection
curl http://127.0.0.1:4200/api/health

# Restart worker
./scripts/orchestration.sh restart dev
```

### Database issues (Docker)

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

---

## Security Considerations

1. **API Access**: Prefect UI exposed on 127.0.0.1 only (not public)
2. **Secrets**: Use `.env` files, not hardcoded in triggers
3. **Database**: PostgreSQL with authentication (Docker)
4. **File Permissions**: Logs and PIDs in protected directories
5. **User Isolation**: Run as non-root user (systemd)

---

## Backup & Recovery

### Configuration Backup

```bash
# Backup all configs
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/

# Restore
tar -xzf config-backup-20250116.tar.gz
```

### Database Backup (Docker)

```bash
# Backup
docker-compose exec postgres pg_dump -U prefect prefect > prefect-$(date +%Y%m%d).sql

# Restore
cat prefect-20250116.sql | docker-compose exec -T postgres psql -U prefect prefect
```

### Flow Run Data

Stored in:

- Script/Systemd: `~/.prefect/` (SQLite)
- Docker: `postgres-data` volume

---

## Upgrading

### Script-Based

```bash
# Stop services
./scripts/orchestration.sh stop

# Pull latest code
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Start services
./scripts/orchestration.sh start
```

### Docker

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d --force-recreate
```

---

## Support

For issues:

1. Check logs: `./scripts/orchestration.sh logs [service]`
2. Verify status: `./scripts/orchestration.sh status`
3. Review Prefect UI: http://127.0.0.1:4200
4. Check this documentation

Common solutions in Troubleshooting section above.

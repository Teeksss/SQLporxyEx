#!/bin/bash
# Enterprise SQL Proxy System - Backup Script
# Created: 2025-05-29 14:45:01 UTC by Teeksss

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="esp_backup_${TIMESTAMP}"

echo "🗄️ Starting backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
echo "📦 Backing up database..."
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/${BACKUP_NAME}_database.sql.gz"

# Application data backup (if needed)
echo "📁 Backing up application data..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" -C /app uploads/ || true

# Cleanup old backups (keep last 30 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "esp_backup_*" -mtime +30 -delete || true

echo "✅ Backup completed: $BACKUP_NAME"

# List current backups
echo "📋 Current backups:"
ls -la "$BACKUP_DIR"/esp_backup_* | tail -10
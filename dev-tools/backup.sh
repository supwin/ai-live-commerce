#!/bin/bash
# Backup Helper Script

echo "💾 Creating backup..."

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
cp ai_live_commerce.db "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ No database to backup"

# Backup logs
cp -r logs "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ No logs to backup"

# Create git commit
git add .
git commit -m "Backup checkpoint: $(date +%Y-%m-%d_%H:%M:%S)" || echo "⚠️ Nothing to commit"

echo "✅ Backup created in $BACKUP_DIR"
echo "✅ Git commit created"


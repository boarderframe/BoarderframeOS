#!/bin/bash
# BoarderframeOS - Old Machine Backup Script
# Run this on your OLD MacBook before resetting it

echo "🏰 BoarderframeOS Backup Script"
echo "==============================="
echo "Run this on your OLD machine to backup data"
echo ""

# Create backup directory
BACKUP_DIR="boarderframeos_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Creating backup in: $BACKUP_DIR"
echo ""

# Backup PostgreSQL database
echo "🗄️  Backing up PostgreSQL database..."
if docker exec boarderframeos_postgres pg_dump -U boarderframe boarderframeos > "$BACKUP_DIR/boarderframeos_postgres.sql" 2>/dev/null; then
    echo "✅ PostgreSQL backup complete"
else
    echo "❌ PostgreSQL backup failed - is the container running?"
fi

# Backup Redis data (if needed)
echo "📊 Backing up Redis data..."
if docker exec boarderframeos_redis redis-cli --rdb "$BACKUP_DIR/redis_backup.rdb" 2>/dev/null; then
    echo "✅ Redis backup complete"
else
    echo "⚠️  Redis backup failed (this is often not critical)"
fi

# Backup Docker volumes
echo "📦 Listing Docker volumes..."
docker volume ls | grep boarderframeos > "$BACKUP_DIR/docker_volumes.txt"

# Backup SQLite databases
echo "💾 Backing up SQLite databases..."
cp -r data/*.db "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  Some SQLite files not found"

# Backup configuration files
echo "⚙️  Backing up configuration..."
cp .env "$BACKUP_DIR/" 2>/dev/null
cp -r configs "$BACKUP_DIR/" 2>/dev/null
cp departments/boarderframeos-departments.json "$BACKUP_DIR/" 2>/dev/null

# Create restore instructions
cat > "$BACKUP_DIR/RESTORE_INSTRUCTIONS.txt" << EOF
BoarderframeOS Backup Restore Instructions
==========================================

1. Copy this entire backup folder to your new machine

2. On the new machine, after starting Docker containers:
   
   # Restore PostgreSQL:
   docker exec -i boarderframeos_postgres psql -U boarderframe -d boarderframeos < boarderframeos_postgres.sql
   
   # Copy SQLite databases:
   cp *.db /path/to/BoarderframeOS/data/
   
   # Copy configuration:
   cp .env /path/to/BoarderframeOS/
   cp -r configs /path/to/BoarderframeOS/
   
3. Run startup.py to verify everything is working

Backup created: $(date)
EOF

# Create tarball for easy transfer
echo ""
echo "📦 Creating compressed archive..."
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"

echo ""
echo "✅ Backup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Transfer ${BACKUP_DIR}.tar.gz to your new machine"
echo "2. Extract: tar -xzf ${BACKUP_DIR}.tar.gz"
echo "3. Follow instructions in RESTORE_INSTRUCTIONS.txt"
echo ""
echo "💡 Quick transfer options:"
echo "   - AirDrop the file to your new Mac"
echo "   - Use a USB drive"
echo "   - Upload to cloud storage"
#!/bin/bash
set -e

# This script runs inside the PostgreSQL container to set up the database
# It will only run if the database is empty (first time initialization)

echo "🔧 Checking if WOL API database needs initialization..."

# Check if verses table exists and has data
VERSE_COUNT=$(psql -U postgres -d wol-api -t -c "SELECT COUNT(*) FROM verses;" 2>/dev/null || echo "0")

if [ "$VERSE_COUNT" -eq "0" ]; then
    echo "📋 Database is empty. Tables will be created, but data population requires manual step."
    echo "ℹ️  After container startup, run:"
    echo "   docker exec -it wol-api_backend_1 python3 scripts/db_manager_docker.py"
    echo "   Then select option 1 to populate with verse data."
else
    echo "✅ Database already contains $VERSE_COUNT verses. Initialization complete."
fi
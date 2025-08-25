#!/bin/bash
set -e

echo "🚀 Starting WOL API services..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
while ! pg_isready -h db -p 5432 -U postgres; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "✅ Database is ready!"

# Run automatic database setup
echo "🔧 Running automatic database setup..."
python3 /home/appuser/scripts/auto_setup_db.py

# Start the database health monitor in the background
echo "🔍 Starting database health monitor..."
python3 /home/appuser/scripts/db_health_monitor.py &
MONITOR_PID=$!

echo "📊 Health monitor started (PID: $MONITOR_PID)"

# Wait a moment for the monitor to start
sleep 2

# Start the main Rust backend
echo "⚡ Starting Rust backend..."
exec cargo run --bin backend
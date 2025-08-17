#!/bin/bash
set -e

echo "🚀 Starting WOL API services..."

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
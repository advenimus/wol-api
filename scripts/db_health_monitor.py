#!/usr/bin/env python3
"""
Database Health Monitor
Continuously monitors database health and auto-restores if needed.
This runs as a background process in the backend container.
"""
import time
import sys
import os
import subprocess
import psycopg2
from datetime import datetime

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_database_health():
    """Check if database tables exist and have data"""
    try:
        conn = psycopg2.connect(
            host="db",
            database="wol-api",
            user="postgres",
            password="postgres",
            connect_timeout=5
        )
        cur = conn.cursor()
        
        # Check if verses table exists and has data
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'verses'
        """)
        table_exists = cur.fetchone()[0] > 0
        
        if table_exists:
            cur.execute("SELECT COUNT(*) FROM verses")
            verse_count = cur.fetchone()[0]
        else:
            verse_count = 0
            
        cur.close()
        conn.close()
        
        return True, table_exists, verse_count
        
    except Exception as e:
        log(f"❌ Error checking database health: {e}")
        return False, False, 0

def restore_database():
    """Restore database using the auto setup script"""
    try:
        log("🔧 Auto-restoring database...")
        
        # Run the auto setup script
        result = subprocess.run([
            "python3", "/home/appuser/scripts/auto_setup_db.py"
        ], capture_output=True, text=True, cwd="/home/appuser")
        
        if result.returncode == 0:
            log("✅ Database auto-restored successfully!")
            return True
        else:
            log(f"❌ Database restore failed: {result.stderr}")
            return False
            
    except Exception as e:
        log(f"❌ Error during database restore: {e}")
        return False

def main():
    """Main monitoring loop"""
    log("🔍 Starting database health monitor...")
    
    # Initial check
    check_interval = 60  # Check every 60 seconds
    consecutive_failures = 0
    max_failures = 3
    
    while True:
        try:
            db_connected, table_exists, verse_count = check_database_health()
            
            if not db_connected:
                consecutive_failures += 1
                log(f"⚠️  Database connection failed (attempt {consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    log("🔄 Database connection failed multiple times, waiting longer...")
                    time.sleep(300)  # Wait 5 minutes before retrying
                    consecutive_failures = 0
                    
            elif not table_exists or verse_count == 0:
                log(f"⚠️  Database needs restoration (tables_exist={table_exists}, verses={verse_count})")
                
                if restore_database():
                    consecutive_failures = 0
                    log("✅ Database restoration completed")
                else:
                    consecutive_failures += 1
                    log(f"❌ Database restoration failed (attempt {consecutive_failures})")
                    
            else:
                if consecutive_failures > 0:
                    log(f"✅ Database health restored - {verse_count:,} verses found")
                consecutive_failures = 0
                
            # Sleep before next check
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            log("👋 Database health monitor stopped by user")
            break
        except Exception as e:
            log(f"❌ Unexpected error in health monitor: {e}")
            time.sleep(check_interval)

if __name__ == "__main__":
    main()
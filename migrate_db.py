import sqlite3
import os

# Path to database
db_path = os.path.join(os.path.dirname(__file__), 'rvm.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column exists
    cursor.execute("PRAGMA table_info(credit_history)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'type' not in columns:
        print("Adding 'type' column to credit_history...")
        cursor.execute("ALTER TABLE credit_history ADD COLUMN type TEXT DEFAULT 'credit' NOT NULL")
        conn.commit()
        print("Migration successful.")
    else:
        print("'type' column already exists.")
        
except Exception as e:
    print(f"Migration failed: {e}")
finally:
    conn.close()

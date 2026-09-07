import sqlite3
import os

def process_data(db_path, user_id):
    """
    Simulates a worker that opens a connection to a DB, but forgets
    to close it if the user doesn't exist (returns early on error).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # RESOURCE LEAK / CLEANUP-ON-FAILURE-MISSING:
        # Returns early without calling conn.close(), leaking the file handle.
        return {"status": "error", "message": "User not found"}
        
    # Happy path
    cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return {"status": "ok"}

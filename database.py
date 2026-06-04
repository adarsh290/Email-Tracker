import sqlite3
import os
from contextlib import contextmanager

DB_FILE = 'agent.db'

def init_db():
    """Initializes the SQLite database with necessary tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table to track processed emails by Message-ID
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_emails (
                message_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table to track deadlines and tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deadlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT,
                summary TEXT,
                deadline TEXT,
                priority TEXT,
                discord_message_id TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(message_id) REFERENCES processed_emails(message_id)
            )
        ''')
        conn.commit()

@contextmanager
def get_db_connection():
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(DB_FILE)
    # Enable row factory to access columns by name
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def is_email_processed(message_id: str) -> bool:
    """Checks if an email has already been processed."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM processed_emails WHERE message_id = ?', (message_id,))
        return cursor.fetchone() is not None

def mark_email_processed(message_id: str):
    """Marks an email as processed."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO processed_emails (message_id) VALUES (?)', (message_id,))
        conn.commit()

def add_deadline(message_id: str, summary: str, deadline: str, priority: str, discord_message_id: str):
    """Adds a new deadline to track."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO deadlines (message_id, summary, deadline, priority, discord_message_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (message_id, summary, deadline, priority, discord_message_id))
        conn.commit()

def update_deadline_status(discord_message_id: str, status: str):
    """Updates the status (Pending/Done) of a deadline based on Discord message ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE deadlines SET status = ? WHERE discord_message_id = ?
        ''', (status, discord_message_id))
        conn.commit()

def get_pending_deadlines():
    """Retrieves all pending deadlines for the daily summary."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM deadlines WHERE status = 'Pending' ORDER BY deadline ASC
        ''')
        return cursor.fetchall()

# Initialize DB on module import
init_db()

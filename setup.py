import sqlite3

def create_connection(db_file='medications.db'):
    conn = sqlite3.connect(db_file)
    return conn

def setup_database(db_file='medications.db'):
    conn = create_connection(db_file)
    cursor = conn.cursor()
    
    # Create the medications table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        strength TEXT NOT NULL,
        dosage_frequency TEXT NOT NULL
    )
    ''')
    
    # Check if the 'description' column exists
    cursor.execute("PRAGMA table_info(medications)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'description' not in columns:
        # Add the 'description' column if it doesn't exist
        cursor.execute('ALTER TABLE medications ADD COLUMN description TEXT')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()
    print("Database setup complete.")
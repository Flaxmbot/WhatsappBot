import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize database
def init_db():
    conn = sqlite3.connect('health_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            language TEXT DEFAULT 'en',
            ai_service TEXT DEFAULT 'gemini'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            phone TEXT PRIMARY KEY,
            name TEXT,
            preferred_language TEXT DEFAULT 'en',
            health_conditions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

# Health check endpoint
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "whatsapp": bool(os.environ.get('WHATSAPP_TOKEN')),
            "gemini": bool(os.environ.get('GEMINI_API_KEY')),
            "groq": bool(os.environ.get('GROQ_API_KEY')),
            "perplexity": bool(os.environ.get('PERPLEXITY_API_KEY'))
        }
    }

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    
    print("Checking health...")
    health = health_check()
    print(health)
    
    print("App is ready to run!")
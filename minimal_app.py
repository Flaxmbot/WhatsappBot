import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
class Config:
    # WhatsApp Business API
    WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_BUSINESS_ACCOUNT_ID = os.environ.get('WHATSAPP_BUSINESS_ACCOUNT_ID')
    VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'health_bot_verify_token_2024')
    
    # App settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

app.config.from_object(Config)

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

# Flask routes
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == Config.VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return challenge
        else:
            logger.error("Webhook verification failed")
            return "Verification token mismatch", 403
    
    return "Missing parameters", 400

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.get_json()
        logger.info(f"Received webhook data: {data}")
        
        # Just acknowledge the message for now
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return "Error", 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "whatsapp": bool(Config.WHATSAPP_TOKEN),
            "app": "running"
        }
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        conn = sqlite3.connect('health_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_phone) FROM conversations')
        unique_users = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "total_conversations": total_conversations,
            "unique_users": unique_users,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": "Unable to fetch stats"}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
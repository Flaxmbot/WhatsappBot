import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import google.generativeai as genai
from groq import Groq
from deep_translator import GoogleTranslator
import sqlite3
from threading import Thread
from twilio.rest import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Configuration ---
class Config:
    # Twilio Credentials
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER') # e.g., 'whatsapp:+14155238886'

    # AI API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
    
    # App Settings
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///health_bot.db')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

app.config.from_object(Config)

# --- Initialize Clients ---
# Initialize Twilio Client
twilio_client = None
if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
    twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
else:
    logger.warning("Twilio credentials not set. WhatsApp features will be disabled.")

# Initialize AI clients
gemini_model = None
groq_client = None
try:
    if Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.5-pro')
    if Config.GROQ_API_KEY:
        groq_client = Groq(api_key=Config.GROQ_API_KEY)
except Exception as e:
    logger.error(f"Error initializing AI clients: {e}")

# --- Database Functions ---
def init_db():
    conn = sqlite3.connect('health_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT NOT NULL,
            message TEXT NOT NULL, response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, language TEXT DEFAULT 'en',
            ai_service TEXT DEFAULT 'gemini'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            phone TEXT PRIMARY KEY, name TEXT, preferred_language TEXT DEFAULT 'en',
            health_conditions TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_conversation(user_phone, message, response, language='en'):
    try:
        conn = sqlite3.connect('health_bot.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_phone, message, response, language) VALUES (?, ?, ?, ?)",
                       (user_phone, message, response, language))
        cursor.execute("INSERT OR IGNORE INTO user_profiles (phone) VALUES (?)", (user_phone,))
        cursor.execute("UPDATE user_profiles SET last_active = ? WHERE phone = ?", (datetime.now(), user_phone))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")

# --- Language and AI Functions ---
def detect_language(text):
    try:
        return GoogleTranslator().detect(text)[0]
    except Exception: return 'en'

def translate_text(text, target_lang='en', source_lang='auto'):
    if target_lang == source_lang: return text
    try:
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except Exception: return text

def get_gemini_response(prompt):
    if not gemini_model: return "AI service is not configured."
    try:
        context = "You are a helpful AI health assistant. Provide accurate, helpful health information, but always include a disclaimer that you are not a medical professional and users should consult a doctor for medical advice."
        response = gemini_model.generate_content(f"{context}\n\nUser question: {prompt}\n\nResponse:")
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return "I'm having trouble processing your request right now."

def get_perplexity_search(query):
    if not Config.PERPLEXITY_API_KEY: return None
    try:
        response = requests.post("https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}"},
            json={"model": "llama-3-sonar-large-32k-online", "messages": [
                {"role": "system", "content": "You are a helpful health information assistant."},
                {"role": "user", "content": f"Search for recent, reliable information about: {query}"}
            ]})
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Perplexity search error: {e}")
    return None

def get_groq_summary(text):
    if not groq_client: return text
    try:
        completion = groq_client.chat.completions.create(model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "Summarize this health information concisely."},
                {"role": "user", "content": text}
            ])
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
    return text

# --- Core Bot Logic ---
def determine_response_strategy(message):
    message_lower = message.lower()
    if any(k in message_lower for k in ['emergency', 'chest pain', 'heart attack', 'stroke']): return 'emergency'
    if any(k in message_lower for k in ['latest', 'recent', 'new treatment']): return 'search_and_reason'
    return 'reason_only'

def process_health_query(message, user_lang='en'):
    strategy = determine_response_strategy(message)
    english_message = translate_text(message, 'en', user_lang)
    
    if strategy == 'emergency':
        response = "If this is a medical emergency, please call your local emergency number immediately. I cannot provide emergency medical care."
    elif strategy == 'search_and_reason':
        search_result = get_perplexity_search(english_message)
        gemini_prompt = f"Based on this recent health information: {search_result}\n\nUser question: {english_message}" if search_result else english_message
        response = get_groq_summary(get_gemini_response(gemini_prompt))
    else: # reason_only
        response = get_groq_summary(get_gemini_response(english_message))
        
    return translate_text(response, user_lang, 'en')

def send_whatsapp_message(to_phone, message_body):
    if not twilio_client:
        logger.error("Twilio client not initialized.")
        return False
    try:
        message = twilio_client.messages.create(
            from_=Config.TWILIO_PHONE_NUMBER,
            body=message_body,
            to=to_phone
        )
        logger.info(f"Message sent to {to_phone} (SID: {message.sid})")
        return True
    except Exception as e:
        logger.error(f"Failed to send Twilio message: {e}")
        return False

def process_message_background(user_phone, user_message):
    user_lang = detect_language(user_message)
    response = process_health_query(user_message, user_lang)
    disclaimer = "\n\n⚠️ This is not medical advice. Please consult a healthcare professional."
    final_response = response + translate_text(disclaimer, user_lang, 'en')
    
    if send_whatsapp_message(user_phone, final_response):
        save_conversation(user_phone, user_message, final_response, user_lang)

# --- Flask Routes ---
@app.route('/twilio/webhook', methods=['POST'])
def handle_twilio_webhook():
    """Handles incoming messages from Twilio."""
    try:
        data = request.values
        user_message = data.get('Body', '').strip()
        user_phone = data.get('From', '')
        
        logger.info(f"Received message from {user_phone}: '{user_message}'")
        
        if user_message and user_phone:
            thread = Thread(target=process_message_background, args=(user_phone, user_message))
            thread.start()
            
    except Exception as e:
        logger.error(f"Error in Twilio webhook: {e}")
        
    return ('', 204) # Return a 204 No Content to acknowledge receipt

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

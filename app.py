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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
class Config:
    WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'health_bot_verify_token_2024')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///health_bot.db')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

app.config.from_object(Config)

# Initialize AI clients
gemini_model = None
groq_client = None

try:
    if Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        logger.warning("GEMINI_API_KEY not set. Gemini features will be disabled.")

    if Config.GROQ_API_KEY:
        groq_client = Groq(api_key=Config.GROQ_API_KEY)
    else:
        logger.warning("GROQ_API_KEY not set. Groq features will be disabled.")
except Exception as e:
    logger.error(f"Error initializing AI clients: {e}")

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

# Language detection and translation functions
def detect_language(text):
    try:
        return GoogleTranslator().detect(text)[0]
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return 'en'

def translate_text(text, target_lang='en', source_lang='auto'):
    if target_lang == source_lang:
        return text
    try:
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

# AI Service Functions
def get_gemini_response(prompt):
    if not gemini_model:
        return "The AI service is not configured."
    try:
        health_context = "You are a helpful AI health assistant. Provide accurate, helpful health information, but always include a disclaimer that you are not a medical professional and users should consult a doctor for medical advice."
        full_prompt = f"{health_context}\n\nUser question: {prompt}\n\nResponse:"
        response = gemini_model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return "I'm having trouble processing your request right now."

def get_perplexity_search(query):
    if not Config.PERPLEXITY_API_KEY:
        return None
    try:
        url = "https://api.perplexity.ai/chat/completions"
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {"role": "system", "content": "You are a helpful health information assistant."},
                {"role": "user", "content": f"Search for recent, reliable information about: {query}"}
            ]
        }
        headers = {
            "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            logger.error(f"Perplexity API error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Perplexity search error: {e}")
        return None

def get_groq_summary(text):
    if not groq_client:
        return text
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Summarize this health information concisely."},
                {"role": "user", "content": text}
            ],
            model="llama-3.1-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return text

# Health-specific response logic
def determine_response_strategy(message):
    message_lower = message.lower()
    if any(keyword in message_lower for keyword in ['emergency', 'chest pain', 'heart attack', 'stroke']):
        return 'emergency'
    if any(keyword in message_lower for keyword in ['latest', 'recent', 'new treatment']):
        return 'search_and_reason'
    return 'reason_only'

def process_health_query(message, user_lang='en'):
    strategy = determine_response_strategy(message)
    english_message = translate_text(message, 'en', user_lang) if user_lang != 'en' else message
    
    if strategy == 'emergency':
        response = "If this is a medical emergency, please call your local emergency number immediately. I cannot provide emergency medical care."
    elif strategy == 'search_and_reason':
        search_result = get_perplexity_search(english_message)
        if search_result:
            gemini_response = get_gemini_response(f"Based on this recent health information: {search_result}\n\nUser question: {english_message}")
            response = get_groq_summary(gemini_response)
        else:
            response = get_gemini_response(english_message)
    else:
        gemini_response = get_gemini_response(english_message)
        response = get_groq_summary(gemini_response)
        
    return translate_text(response, user_lang, 'en') if user_lang != 'en' else response

# WhatsApp API functions
def send_whatsapp_message(to_phone, message):
    try:
        url = f"https://graph.facebook.com/v18.0/{Config.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {Config.WHATSAPP_TOKEN}", "Content-Type": "application/json"}
        data = {"messaging_product": "whatsapp", "to": to_phone, "type": "text", "text": {"body": message}}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"Message sent to {to_phone}")
            return True
        else:
            logger.error(f"Failed to send message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False

def save_conversation(user_phone, message, response, language='en'):
    try:
        conn = sqlite3.connect('health_bot.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_phone, message, response, language) VALUES (?, ?, ?, ?)", (user_phone, message, response, language))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")

# Flask routes
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == Config.VERIFY_TOKEN:
        return challenge
    else:
        return "Verification token mismatch", 403

def process_message_background(user_phone, user_message):
    user_lang = detect_language(user_message)
    response = process_health_query(user_message, user_lang)
    disclaimer = "\n\n⚠️ This is not medical advice. Please consult a healthcare professional for medical concerns."
    final_response = response + translate_text(disclaimer, user_lang, 'en')
    
    if send_whatsapp_message(user_phone, final_response):
        save_conversation(user_phone, user_message, final_response, user_lang)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    if 'entry' in data:
        for entry in data['entry']:
            for change in entry['changes']:
                if change['field'] == 'messages':
                    for message in change['value']['messages']:
                        if message['type'] == 'text':
                            user_phone = message['from']
                            user_message = message['text']['body']
                            thread = Thread(target=process_message_background, args=(user_phone, user_message))
                            thread.start()
    return "OK", 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
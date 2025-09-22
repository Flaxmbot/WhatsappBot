import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import google.generativeai as genai
from groq import Groq
import asyncio
import aiohttp
from googletrans import Translator
import re
from werkzeug.security import generate_password_hash
import sqlite3
from threading import Thread
import time

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
    
    # AI API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///health_bot.db')
    
    # App settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

app.config.from_object(Config)

# Initialize AI clients
genai.configure(api_key=Config.GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')
groq_client = Groq(api_key=Config.GROQ_API_KEY)
translator = Translator()

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
        detection = translator.detect(text)
        return detection.lang if detection.confidence > 0.7 else 'en'
    except:
        return 'en'

def translate_text(text, target_lang='en', source_lang='auto'):
    if target_lang == 'en' and source_lang == 'en':
        return text
    try:
        translated = translator.translate(text, dest=target_lang, src=source_lang)
        return translated.text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

# AI Service Functions
async def get_gemini_response(prompt, context="health"):
    try:
        health_context = """
        You are a helpful AI health assistant. Provide accurate, helpful health information while:
        1. Never replacing professional medical advice
        2. Encouraging users to consult healthcare providers for serious concerns
        3. Providing general wellness tips and health information
        4. Being empathetic and supportive
        5. Keeping responses concise but informative
        6. Always disclaiming that this is not medical advice
        """
        
        full_prompt = f"{health_context}\n\nUser question: {prompt}\n\nResponse:"
        
        response = gemini_model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return "I'm having trouble processing your request right now. Please try again later."

async def get_perplexity_search(query):
    try:
        url = "https://api.perplexity.ai/chat/completions"
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful health information assistant. Search for current, accurate health information and provide concise, helpful responses with sources when possible."
                },
                {
                    "role": "user",
                    "content": f"Search for recent, reliable information about: {query}"
                }
            ],
            "max_tokens": 300,
            "temperature": 0.2,
            "top_p": 0.9,
            "search_domain_filter": ["pubmed.ncbi.nlm.nih.gov", "mayoclinic.org", "who.int", "cdc.gov", "nih.gov"]
        }
        
        headers = {
            "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.error(f"Perplexity API error: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Perplexity search error: {e}")
        return None

def get_groq_summary(text):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a text summarizer. Create a concise, clear summary of health-related content in 2-3 sentences maximum. Focus on key actionable information."
                },
                {
                    "role": "user",
                    "content": f"Summarize this health information concisely: {text}"
                }
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.3,
            max_tokens=150,
            top_p=1,
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return text[:200] + "..." if len(text) > 200 else text

# Health-specific response logic
def determine_response_strategy(message):
    message_lower = message.lower()
    
    # Emergency keywords
    emergency_keywords = ['emergency', 'urgent', 'chest pain', 'heart attack', 'stroke', 'bleeding', 'unconscious', 'breathing problem']
    if any(keyword in message_lower for keyword in emergency_keywords):
        return 'emergency'
    
    # Search-worthy queries (current info, specific conditions)
    search_keywords = ['latest', 'recent', 'new treatment', 'current research', 'news', 'study', 'breakthrough']
    if any(keyword in message_lower for keyword in search_keywords):
        return 'search_and_reason'
    
    # Simple health queries
    health_keywords = ['symptom', 'pain', 'treatment', 'medication', 'exercise', 'diet', 'nutrition', 'wellness']
    if any(keyword in message_lower for keyword in health_keywords):
        return 'reason_only'
    
    return 'general'

async def process_health_query(message, user_lang='en'):
    strategy = determine_response_strategy(message)
    
    # Translate to English if needed
    english_message = translate_text(message, 'en', user_lang) if user_lang != 'en' else message
    
    if strategy == 'emergency':
        response = """🚨 MEDICAL EMERGENCY DETECTED 🚨

If this is a medical emergency:
• Call your local emergency number immediately (911, 102, etc.)
• Go to the nearest emergency room
• Contact emergency services

I cannot provide emergency medical care. Please seek immediate professional help."""
        
    elif strategy == 'search_and_reason':
        # First search for current info
        search_result = await get_perplexity_search(english_message)
        if search_result:
            # Then reason about it with Gemini
            reasoning_prompt = f"Based on this recent health information: {search_result}\n\nUser question: {english_message}\n\nProvide helpful guidance:"
            gemini_response = await get_gemini_response(reasoning_prompt)
            # Summarize with Groq
            response = get_groq_summary(f"{gemini_response}\n\nRecent info: {search_result}")
        else:
            response = await get_gemini_response(english_message)
            
    elif strategy == 'reason_only':
        gemini_response = await get_gemini_response(english_message)
        response = get_groq_summary(gemini_response)
        
    else:
        response = await get_gemini_response(english_message)
    
    # Translate back to user's language if needed
    if user_lang != 'en':
        response = translate_text(response, user_lang, 'en')
    
    return response

# WhatsApp API functions
def send_whatsapp_message(to_phone, message):
    try:
        url = f"https://graph.facebook.com/v18.0/{Config.WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            logger.info(f"Message sent successfully to {to_phone}")
            return True
        else:
            logger.error(f"Failed to send message: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False

def save_conversation(user_phone, message, response, language='en', ai_service='gemini'):
    try:
        conn = sqlite3.connect('health_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (user_phone, message, response, language, ai_service)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_phone, message, response, language, ai_service))
        
        # Update user last active
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles (phone, last_active)
            VALUES (?, ?)
        ''', (user_phone, datetime.now()))
        
        conn.commit()
        conn.close()
        logger.info(f"Conversation saved for {user_phone}")
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")

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
        
        if 'entry' in data:
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if change['field'] == 'messages':
                            value = change['value']
                            
                            if 'messages' in value:
                                for message in value['messages']:
                                    if message['type'] == 'text':
                                        user_phone = message['from']
                                        user_message = message['text']['body']
                                        
                                        # Process message in background
                                        thread = Thread(target=process_message_background, 
                                                      args=(user_phone, user_message))
                                        thread.start()
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return "Error", 500

def process_message_background(user_phone, user_message):
    try:
        # Detect language
        user_lang = detect_language(user_message)
        
        # Process the health query
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(process_health_query(user_message, user_lang))
        loop.close()
        
        # Add disclaimer
        disclaimer = "\n\n⚠️ This is not medical advice. Please consult a healthcare professional for medical concerns."
        if user_lang != 'en':
            disclaimer = translate_text(disclaimer, user_lang, 'en')
        
        final_response = response + disclaimer
        
        # Send response
        if send_whatsapp_message(user_phone, final_response):
            save_conversation(user_phone, user_message, final_response, user_lang)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        error_message = "Sorry, I'm having technical difficulties. Please try again later."
        send_whatsapp_message(user_phone, error_message)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "whatsapp": bool(Config.WHATSAPP_TOKEN),
            "gemini": bool(Config.GEMINI_API_KEY),
            "groq": bool(Config.GROQ_API_KEY),
            "perplexity": bool(Config.PERPLEXITY_API_KEY)
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
        
        cursor.execute('SELECT language, COUNT(*) FROM conversations GROUP BY language')
        language_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            "total_conversations": total_conversations,
            "unique_users": unique_users,
            "language_distribution": language_stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": "Unable to fetch stats"}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import google.generativeai as genai
from groq import Groq
import sqlite3
from threading import Thread
from twilio.rest import Client

# Configure logging to be detailed
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
logger.info("Configuration loaded.")

# --- Initialize Clients ---
twilio_client = None
if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")
else:
    logger.warning("Twilio credentials not set. WhatsApp features will be disabled.")

gemini_model = None
groq_client = None
try:
    if Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Gemini client initialized successfully with gemini-2.5-flash.")
    else:
        logger.warning("GEMINI_API_KEY not set. Gemini features will be disabled.")

    if Config.GROQ_API_KEY:
        groq_client = Groq(api_key=Config.GROQ_API_KEY)
        logger.info("Groq client initialized successfully.")
    else:
        logger.warning("GROQ_API_KEY not set. Groq features will be disabled.")
except Exception as e:
    logger.error(f"Error initializing AI clients: {e}")

# --- Database Functions ---
def init_db():
    logger.info("Initializing database...")
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
    logger.info("Database initialized successfully.")

def save_conversation(user_phone, message, response, language='en'):
    logger.info(f"Saving conversation for user {user_phone}...")
    try:
        conn = sqlite3.connect('health_bot.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_phone, message, response, language) VALUES (?, ?, ?, ?)",
                       (user_phone, message, response, language))
        cursor.execute("INSERT OR IGNORE INTO user_profiles (phone) VALUES (?)", (user_phone,))
        cursor.execute("UPDATE user_profiles SET last_active = ? WHERE phone = ?", (datetime.now(), user_phone))
        conn.commit()
        conn.close()
        logger.info(f"Conversation for {user_phone} saved successfully.")
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")

# --- Language and AI Functions ---
def translate_with_gemini(text, target_lang):
    """Detects source language and translates text using Gemini, returning a dictionary."""
    logger.info(f"Starting translation process for target language '{target_lang}'...")
    try:
        prompt = f"""Analyze the following text. First, identify its source language. Second, translate it to {target_lang}.
        Provide the output ONLY as a valid JSON object with two keys: "detected_language" and "translated_text".
        Text to analyze: "{text}"
        """
        response = gemini_model.generate_content(prompt)
        
        # Clean the response to ensure it's valid JSON
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(cleaned_response)
        
        logger.info(f"Gemini translation successful. Detected language: {result.get('detected_language')}")
        return result
    except Exception as e:
        logger.error(f"Gemini translation/detection failed: {e}. Defaulting to English.")
        return {"detected_language": "en", "translated_text": text}

def get_gemini_response(prompt, model_name='gemini-2.5-flash'):
    if not gemini_model: return "AI service is not configured."
    logger.info(f"Getting response from Gemini model: {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        context = """
        You are Dr. AI, an AI Health Advisor with the persona of an experienced, empathetic, and professional doctor.
        Your communication must be:
        1.  **Direct and Clear:** Address the user directly.
        2.  **Concise:** Provide point-to-point health information without conversational filler.
        3.  **Structured:** Use bullet points or numbered lists for clarity.
        4.  **Reassuring but Professional:** Maintain a tone that is both comforting and authoritative.
        5.  **Disclaimer-First:** This is not a substitute for professional medical advice. Always encourage users to consult a real doctor for any health concerns.
        """
        response = model.generate_content(f"{context}\n\nHere is the user's question: {prompt}\n\nYour response:")
        logger.info(f"Successfully received response from {model_name}.")
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error with model {model_name}: {e}")
        return None

def get_perplexity_search(query):
    if not Config.PERPLEXITY_API_KEY: return None
    logger.info(f"Searching Perplexity (sonar) for: '{query}'")
    try:
        response = requests.post("https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}"},
            json={"model": "llama-3-sonar-large-32k-online", "messages": [
                {"role": "system", "content": "You are a health information search expert. Find the most relevant, recent, and reliable medical information for the user's query."},
                {"role": "user", "content": f"Search for: {query}"}
            ]})
        if response.status_code == 200:
            logger.info("Perplexity search successful.")
            return response.json()['choices'][0]['message']['content']
        else:
            logger.error(f"Perplexity API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Perplexity search error: {e}")
    return None

def get_groq_summary(text):
    if not groq_client: return None
    model_to_use = "llama3-70b-8192"
    logger.info(f"Summarizing text with Groq model {model_to_use}...")
    try:
        completion = groq_client.chat.completions.create(model=model_to_use,
            messages=[
                {"role": "system", "content": "You are a medical summarizer. Refine the following health information into a concise, point-to-point summary for a patient. Maintain a professional and clear tone. Remove conversational filler and focus only on key actionable advice and critical information."},
                {"role": "user", "content": text}
            ])
        logger.info("Groq summary successful.")
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
    return None

# --- Core Bot Logic ---
def determine_response_strategy(message):
    message_lower = message.lower()
    strategy = 'reason_only' # Default strategy
    if any(k in message_lower for k in ['emergency', 'chest pain', 'heart attack', 'stroke']):
        strategy = 'emergency'
    elif any(k in message_lower for k in ['latest', 'recent', 'new treatment']):
        strategy = 'search_and_reason'
    logger.info(f"Determined response strategy: '{strategy}'")
    return strategy

def process_health_query(message_in_english):
    strategy = determine_response_strategy(message_in_english)
    
    response = ""
    if strategy == 'emergency':
        response = "If this is a medical emergency, please call your local emergency number immediately. I cannot provide emergency medical care."
    elif strategy == 'search_and_reason':
        search_result = get_perplexity_search(message_in_english)
        if search_result:
            gemini_prompt = f"Based on this recent health information: {search_result}\n\nUser question: {message_in_english}"
            gemini_response = get_gemini_response(gemini_prompt)
            response = get_groq_summary(gemini_response) or gemini_response
        else:
            logger.warning("Perplexity search failed. Falling back to Gemini directly.")
            response = get_gemini_response(message_in_english)
    else: # reason_only
        gemini_response = get_gemini_response(message_in_english)
        response = get_groq_summary(gemini_response) or gemini_response
        
    logger.info(f"Generated final response for user in English.")
    return response

def send_whatsapp_message(to_phone, message_body):
    if not twilio_client:
        logger.error("Cannot send message, Twilio client not initialized.")
        return False
    logger.info(f"Attempting to send message to {to_phone} via Twilio...")
    try:
        message = twilio_client.messages.create(
            from_=Config.TWILIO_PHONE_NUMBER,
            body=message_body,
            to=to_phone
        )
        logger.info(f"Message sent successfully to {to_phone} (SID: {message.sid})")
        return True
    except Exception as e:
        logger.error(f"Failed to send Twilio message: {e}")
        return False

def process_message_background(user_phone, user_message):
    logger.info(f"Starting background processing for user {user_phone}.")
    try:
        # 1. Translate user message to English and detect their language
        translation_result = translate_with_gemini(user_message, "English")
        english_message = translation_result['translated_text']
        user_lang = translation_result['detected_language']
        logger.info(f"User language is '{user_lang}', translated message is '{english_message}'")

        # 2. Process the query in English to get the core response
        response_in_english = process_health_query(english_message)

        # 3. Add disclaimer
        disclaimer = "\n\n---\n*This is not a substitute for professional medical advice. Please consult a doctor for any health concerns.*"
        full_response_in_english = response_in_english + disclaimer

        # 4. Translate the full response back to the user's language
        final_translation_result = translate_with_gemini(full_response_in_english, user_lang)
        final_response = final_translation_result['translated_text']
        
        # 5. Send and save
        if send_whatsapp_message(user_phone, final_response):
            save_conversation(user_phone, user_message, final_response, user_lang)
        else:
            logger.error(f"Failed to send final response to {user_phone}.")
    except Exception as e:
        logger.error(f"Unhandled exception in background processor: {e}")
    logger.info(f"Finished background processing for {user_phone}.")

# --- Flask Routes ---
@app.route('/webhook', methods=['POST'])
def handle_twilio_webhook():
    """Handles incoming messages from Twilio."""
    logger.info("Received request on /webhook")
    try:
        data = request.values
        user_message = data.get('Body', '').strip()
        user_phone = data.get('From', '')
        
        logger.info(f"Parsed message from {user_phone}: '{user_message}'")
        
        if user_message and user_phone:
            thread = Thread(target=process_message_background, args=(user_phone, user_message))
            thread.start()
            logger.info(f"Started background thread for {user_phone}.")
            
    except Exception as e:
        logger.error(f"Error in Twilio webhook handler: {e}")
        
    return ('', 204) # Return a 204 No Content to acknowledge receipt

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


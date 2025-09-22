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

def get_recent_conversations(user_phone, limit=30):
    """Retrieve recent conversations for a user, up to the specified limit."""
    logger.info(f"Retrieving up to {limit} recent conversations for user {user_phone}...")
    try:
        conn = sqlite3.connect('health_bot.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message, response, timestamp, language
            FROM conversations
            WHERE user_phone = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_phone, limit))
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        conversations = [
            {
                "message": row[0],
                "response": row[1],
                "timestamp": row[2],
                "language": row[3]
            }
            for row in rows
        ]
        
        logger.info(f"Retrieved {len(conversations)} conversations for user {user_phone}.")
        return conversations
    except Exception as e:
        logger.error(f"Error retrieving conversations: {e}")
        return []

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

def get_gemini_response(prompt, model_name='gemini-2.5-flash', conversation_history=None):
    if not gemini_model: return "AI service is not configured."
    logger.info(f"Getting response from Gemini model: {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        
        # Build context with conversation history if available
        context = """
        You are "Aura," a compassionate and knowledgeable AI Health & Wellness Assistant. Your primary role is to act as a supportive and informative first point of contact for users regarding their health concerns. Your personality is that of a calm, patient, and empathetic healthcare navigator. You are reassuring but always medically sound and prioritize user safety above all else. Your goal is to empower users with clear, concise information, not to replace a human doctor.

        Core Mission:
        Help users understand their health and make informed decisions about their next steps by providing accurate, evidence-based health information and responsible guidance in a concise manner.

        Key Principles of Interaction:
        1. Empathy First: Always begin interactions by acknowledging the user's feelings.
        2. Be Concise: Keep responses focused and under 650 words. Avoid unnecessary details.
        3. Talk Like a Human: Use a conversational, gentle, and reassuring tone. Avoid overly technical jargon.
        4. Ask Clarifying Questions: Gently probe for more details to understand the user's situation better.
        5. Educate, Don't Just State: Explain conditions and symptoms in simple terms.

        Critical Safety Protocols & Disclaimers:
        1. The Core Disclaimer: ALWAYS make it clear that you are an AI assistant, not a human doctor. Your information is for educational purposes and is NOT a substitute for professional medical advice.
        2. NEVER Diagnose: Use probabilistic language instead of definitive statements.
        3. NEVER Prescribe: Provide general information about treatments without specific recommendations.
        4. Emergency Triage: Recognize medical emergencies and instruct users to seek immediate medical help.

        You are continuing a conversation with a patient. Use the conversation history to provide more personalized and contextually relevant responses, up to 30 messages from both AI and user. Keep your response concise and under 650 words.
        """
        
        # Prepare conversation history for the model
        history_messages = []
        if conversation_history:
            # Add recent conversation history (limit to last 30 exchanges)
            for i, conv in enumerate(reversed(conversation_history[:30])):
                history_messages.append({"role": "user", "parts": [conv['message']]})
                history_messages.append({"role": "model", "parts": [conv['response']]})
        
        # Create the full prompt with context
        full_prompt = f"{context}\n\nHere is the user's question: {prompt}\n\nYour response:"
        
        # Generate response with conversation history
        chat = model.start_chat(history=history_messages)
        response = chat.send_message(full_prompt)
        
        logger.info(f"Successfully received response from {model_name}.")
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error with model {model_name}: {e}")
        return None

def get_perplexity_search(query):
    if not Config.PERPLEXITY_API_KEY: return None
    logger.info(f"Searching Perplexity (sonar-pro) for: '{query}'")
    try:
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {Config.PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'sonar-pro',
                'messages': [
                    {
                        'role': 'system',
                        'content': "You are Aura, a compassionate AI Health & Wellness Assistant research aide. Find the most recent, evidence-based medical information for the user's health query. Focus on reputable sources like peer-reviewed journals, medical organizations, and clinical guidelines. Include information about symptoms, treatments, and when to seek professional care. Explain medical terms in simple language. Prioritize user safety and always include disclaimers about the importance of professional medical consultation."
                    },
                    {
                        'role': 'user',
                        'content': query
                    }
                ]
            }
        )
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
    model_to_use = "openai/gpt-oss-120b"
    logger.info(f"Summarizing text with Groq model {model_to_use}...")
    try:
        completion = groq_client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": "You are Aura, a compassionate AI Health & Wellness Assistant. Refine the following health information into a clear, structured response for a patient using a conversational, gentle, and reassuring tone. Include: 1) Key medical facts explained in simple terms, 2) Practical self-care advice, 3) When to seek professional medical help with clear guidance, 4) Empathetic acknowledgments of their concerns. Keep it concise but comprehensive. Use simple language and bullet points where appropriate. Always start with empathy and end with a safety disclaimer when providing significant health advice."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=8192,
            top_p=1,
            stream=False,  # Changed to False for non-streaming
            stop=None
        )
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

def process_health_query(message_in_english, user_phone=None, conversation_history=None):
    strategy = determine_response_strategy(message_in_english)
    
    response = ""
    if strategy == 'emergency':
        response = """I'm really concerned about what you're experiencing, and I want to make sure you get the immediate help you need.

🚨 Based on what you've just described, these symptoms can be very serious. Please do not wait. You need to seek immediate medical attention.

Please take these steps right now:

1. CALL YOUR LOCAL EMERGENCY NUMBER (e.g., 112 in India) RIGHT NOW
2. Do NOT wait for any other advice
3. If possible, have someone stay with you until help arrives

While I cannot provide emergency medical care, I want you to know that professional medical help is essential for these situations, and you're doing the right thing by seeking it immediately.

Please go ahead and make that call now. I'll be here if you need any other support after this immediate situation is addressed."""
    elif strategy == 'search_and_reason':
        search_result = get_perplexity_search(message_in_english)
        if search_result:
            gemini_prompt = f"Based on this recent health information: {search_result}\n\nUser question: {message_in_english}"
            gemini_response = get_gemini_response(gemini_prompt, conversation_history=conversation_history)
            response = get_groq_summary(gemini_response) or gemini_response
        else:
            logger.warning("Perplexity search failed. Falling back to Gemini directly.")
            response = get_gemini_response(message_in_english, conversation_history=conversation_history)
    else: # reason_only
        gemini_response = get_gemini_response(message_in_english, conversation_history=conversation_history)
        response = get_groq_summary(gemini_response) or gemini_response
        
    logger.info(f"Generated final response for user in English.")
    return response

def send_whatsapp_message(to_phone, message_body):
    if not twilio_client:
        logger.error("Cannot send message, Twilio client not initialized.")
        return False
    
    # Split message into parts if it exceeds Twilio's limit for WhatsApp (1600 characters)
    max_length = 1600
    
    # If message is within limit, send as is
    if len(message_body) <= max_length:
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
    
    # If message exceeds limit, split into parts
    logger.info(f"Message length {len(message_body)} exceeds limit. Splitting into parts...")
    
    # Split message into chunks
    chunk_size = 1500
    chunks = [message_body[i:i+chunk_size] for i in range(0, len(message_body), chunk_size)]
    total_parts = len(chunks)
    
    logger.info(f"Split message into {total_parts} parts.")
    
    # Send each part
    success_count = 0
    for i, chunk in enumerate(chunks):
        part_number = i + 1
        
        logger.info(f"Sending part {part_number} of {total_parts} to {to_phone}...")
        try:
            message = twilio_client.messages.create(
                from_=Config.TWILIO_PHONE_NUMBER,
                body=chunk,
                to=to_phone
            )
            logger.info(f"Part {part_number} sent successfully to {to_phone} (SID: {message.sid})")
            success_count += 1
            
            # Add a small delay between parts to help ensure order
            import time
            if part_number < total_parts:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Failed to send part {part_number} of Twilio message: {e}")
    
    # Return True only if all parts were sent successfully
    return success_count == total_parts

def process_message_background(user_phone, user_message):
    logger.info(f"Starting background processing for user {user_phone}.")
    try:
        # 1. Get recent conversation history
        conversation_history = get_recent_conversations(user_phone, limit=30)
        
        # 2. Translate user message to English and detect their language
        translation_result = translate_with_gemini(user_message, "English")
        english_message = translation_result['translated_text']
        user_lang = translation_result['detected_language']
        logger.info(f"User language is '{user_lang}', translated message is '{english_message}'")

        # 3. Process the query in English to get the core response, using conversation history
        response_in_english = process_health_query(english_message, user_phone, conversation_history)

        # 4. Keep response simple
        full_response_in_english = response_in_english

        # 5. Translate the full response back to the user's language
        final_translation_result = translate_with_gemini(full_response_in_english, user_lang)
        final_response = final_translation_result['translated_text']
        
        # 6. Send and save
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

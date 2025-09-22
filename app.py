import os
import json
import logging
import requests
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Configuration ---
WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'health_bot_verify_token_2024')

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Handles webhook verification challenges from Facebook."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return challenge
    else:
        logger.error("Webhook verification failed.")
        return "Verification token mismatch", 403

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handles incoming messages from WhatsApp."""
    data = request.get_json()
    logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")
    
    try:
        # Extract message details
        entry = data['entry'][0]
        change = entry['changes'][0]
        message_data = change['value']['messages'][0]
        
        if message_data['type'] == 'text':
            user_phone = message_data['from']
            user_message = message_data['text']['body']
            
            # --- Echo the message back to the user ---
            send_whatsapp_message(user_phone, f"Prototype is working! You said: '{user_message}'")
            
    except (KeyError, IndexError) as e:
        logger.error(f"Could not parse incoming message: {e}")
        
    return "OK", 200

def send_whatsapp_message(to_phone, message):
    """Sends a message via the WhatsApp Business API."""
    if not all([WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID]):
        logger.error("Missing critical environment variables.")
        return

    try:
        url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message}
        }
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            logger.info(f"Successfully sent message to {to_phone}")
        else:
            logger.error(f"Failed to send message: {response.text}")
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Provides a simple health check endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
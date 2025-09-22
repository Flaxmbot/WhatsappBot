import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables from .env file for local testing
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Fetch configuration from environment variables
WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
RECIPIENT_PHONE_NUMBER = "918273707186" # Default number for the broadcast

def send_whatsapp_message(to_phone, message):
    """Sends a single WhatsApp message."""
    if not all([WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID]):
        logger.error("Missing WHATSAPP_TOKEN or WHATSAPP_PHONE_NUMBER_ID in environment variables.")
        return False
    try:
        url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
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
            logger.error(f"Failed to send message to {to_phone}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"An exception occurred while sending message: {e}")
        return False

def broadcast_startup_message():
    """Broadcasts a startup message to the default recipient."""
    logger.info(f"Attempting to send startup broadcast to {RECIPIENT_PHONE_NUMBER}...")
    startup_message = "Hello! The Health AI Chatbot is now online and ready to assist you. 🤖"
    
    if send_whatsapp_message(RECIPIENT_PHONE_NUMBER, startup_message):
        logger.info("Startup broadcast sent successfully.")
    else:
        logger.error("Failed to send startup broadcast.")

if __name__ == '__main__':
    broadcast_startup_message()
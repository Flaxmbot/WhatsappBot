# WhatsApp AI Health Chatbot - Complete Setup Guide

## Overview
This is a production-ready WhatsApp chatbot that provides AI-powered health information using:
- **Gemini AI** for health reasoning and advice
- **Perplexity API** for real-time health information search  
- **Groq** for text summarization and concise responses
- **Google Translate** for multilingual support
- **SQLite** for conversation storage
- **Flask** web framework for webhook handling

## 🚀 Quick Start

### 1. Clone and Setup Project
```bash
git clone <your-repo>
cd whatsapp-health-chatbot
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file from `.env.example` and fill in all required values.

### 3. Deploy to Render.com
- Push code to GitHub repository
- Connect to Render.com
- Use the provided `render.yaml` configuration
- Add environment variables in Render dashboard

---

## 📱 WhatsApp Business API Setup (Detailed)

### Step 1: Facebook Developer Account
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "Get Started" and create a developer account
3. Verify your account with phone number and email

### Step 2: Create Facebook App
1. Click "Create App" → "Business" → Continue
2. Fill in:
   - **App Name**: `Health Chatbot` (or your choice)
   - **App Contact Email**: Your email
   - **Business Account**: Create or select existing
3. Click "Create App"

### Step 3: Add WhatsApp Business Product
1. In your app dashboard, click "Add Product"
2. Find "WhatsApp" and click "Set Up"
3. You'll see the WhatsApp Business API configuration page

### Step 4: Get Temporary Access Token (For Testing)
1. In WhatsApp > API Setup, you'll see:
   - **Temporary Access Token** (24 hours only)
   - **Phone Number ID** 
   - **WhatsApp Business Account ID**
2. Copy these values for initial testing

### Step 5: Set Up Webhook
1. In WhatsApp > Configuration > Webhook
2. Set:
   - **Callback URL**: `https://your-app.onrender.com/webhook`
   - **Verify Token**: `health_bot_verify_token_2024`
3. Click "Verify and Save"
4. Subscribe to webhook fields:
   - ✅ messages
   - ✅ message_deliveries (optional)

### Step 6: Get Permanent Access Token

#### Option A: Business Verification (Recommended)
1. Go to Business Settings → Security Center
2. Complete business verification process:
   - Upload business documents
   - Verify business details
   - Complete review process (1-3 days)
3. Once verified, token becomes permanent

#### Option B: System User Token (Alternative)
1. Go to Business Settings → System Users
2. Create new System User:
   - **Name**: `Health Bot System User`
   - **Role**: Admin
3. Generate token:
   - Select your app
   - Grant permissions: `whatsapp_business_messaging`
   - Generate token (This is permanent)

### Step 7: Phone Number Registration
For production use beyond test number:
1. Go to WhatsApp > API Setup > Phone Numbers
2. Add your business phone number
3. Complete phone number verification
4. Update `WHATSAPP_PHONE_NUMBER_ID` with new number ID

---

## 🔑 API Keys Setup

### Gemini AI API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Copy key to `GEMINI_API_KEY`

### Groq API Key  
1. Go to [Groq Console](https://console.groq.com/keys)
2. Create account and generate API key
3. Copy key to `GROQ_API_KEY`

### Perplexity API Key
1. Go to [Perplexity AI](https://www.perplexity.ai/settings/api)
2. Create account and generate API key  
3. Copy key to `PERPLEXITY_API_KEY`

---

## 🚢 Render.com Deployment

### Step 1: Prepare Repository
1. Push your code to GitHub repository
2. Ensure `render.yaml` is in root directory

### Step 2: Create Render Service
1. Go to [Render.com](https://render.com) 
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Render will auto-detect Python app

### Step 3: Configure Environment Variables
In Render dashboard, add these environment variables:

```bash
WHATSAPP_TOKEN=your_permanent_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id  
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
VERIFY_TOKEN=health_bot_verify_token_2024
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
SECRET_KEY=auto_generated_by_render
```

### Step 4: Deploy
1. Click "Create Web Service"
2. Render will automatically:
   - Install dependencies from `requirements.txt`
   - Start app with gunicorn
   - Provide you with app URL

### Step 5: Update Webhook URL
1. Copy your Render app URL: `https://your-app.onrender.com`
2. Update WhatsApp webhook URL to: `https://your-app.onrender.com/webhook`

---

## 🔧 Configuration Details

### Environment Variables Explained

| Variable | Description | Required |
|----------|-------------|----------|
| `WHATSAPP_TOKEN` | Permanent access token from Facebook | ✅ |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone number ID from WhatsApp Business | ✅ |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Business account ID | ✅ |
| `VERIFY_TOKEN` | Custom token for webhook verification | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `GROQ_API_KEY` | Groq API key | ✅ |
| `PERPLEXITY_API_KEY` | Perplexity search API key | ✅ |
| `SECRET_KEY` | Flask secret key | ✅ |

### Webhook Configuration
- **URL**: `https://your-app.onrender.com/webhook`
- **Method**: POST
- **Verify Token**: `health_bot_verify_token_2024`
- **Fields**: messages, message_deliveries

---

## 🧪 Testing Your Bot

### 1. Test Webhook
```bash
curl -X GET "https://your-app.onrender.com/webhook?hub.mode=subscribe&hub.verify_token=health_bot_verify_token_2024&hub.challenge=test"
```
Should return: `test`

### 2. Health Check
```bash
curl https://your-app.onrender.com/health
```
Should return JSON with service status.

### 3. Send Test Message
1. Add test WhatsApp number to your business account
2. Send message: "Hello, I have a headache"
3. Bot should respond with AI-generated health advice

---

## 🌍 Multilingual Support

The bot automatically:
1. Detects user's language
2. Translates to English for AI processing
3. Translates response back to user's language

Supported languages: All languages supported by Google Translate (100+)

---

## 📊 Monitoring & Analytics

### Built-in Endpoints
- `/health` - Service health check
- `/stats` - Conversation statistics

### Database Tables
- `conversations` - All chat history
- `user_profiles` - User preferences and activity

---

## 🔒 Security Features

- Webhook signature verification
- Environment variable security
- Input sanitization
- Rate limiting ready
- SQL injection protection

---

## 📈 Scaling Considerations

### Free Tier Limits
- **Render**: 750 hours/month, sleeps after 15min inactivity
- **Facebook**: 1000 messages/month on test numbers
- **Gemini**: 15 RPM, 1.5M tokens/minute
- **Groq**: 30 RPM, 6000 tokens/minute  
- **Perplexity**: 20 RPM

### Production Scaling
- Upgrade to Render paid plan ($7+/month)
- Business verification for unlimited WhatsApp messages
- Implement Redis for session management
- Add PostgreSQL for better database performance

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Messages
- Check webhook URL is correct and HTTPS
- Verify token matches exactly  
- Check Render logs for errors

#### 2. Bot Not Responding
- Check API keys are valid
- Verify environment variables in Render
- Check `/health` endpoint

#### 3. Messages in Wrong Language  
- Check Google Translate service
- Verify language detection logic
- Test with different language inputs

#### 4. Rate Limiting Errors
- Check API quotas
- Implement exponential backoff
- Add request queuing

### Debug Commands
```bash
# Check Render logs
render logs --tail --service your-service-name

# Test local setup
python app.py

# Check environment variables
echo $WHATSAPP_TOKEN
```

---

## 📞 Support & Maintenance

### Regular Tasks
- Monitor API usage and quotas
- Check webhook delivery status  
- Review conversation logs
- Update AI model versions

### Support Contacts
- **Facebook WhatsApp**: [Business Help Center](https://business.facebook.com/help)
- **Render**: [Documentation](https://render.com/docs)
- **API Issues**: Check respective API documentation

---

## 🎯 Next Steps

1. **Complete Facebook Business Verification** for permanent token
2. **Deploy to Render.com** following the guide
3. **Test thoroughly** with different languages and health queries  
4. **Monitor performance** and optimize based on usage
5. **Scale** based on user growth and requirements

Your WhatsApp AI Health Chatbot is now ready for production use! 🚀
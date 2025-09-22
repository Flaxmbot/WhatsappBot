# 🏥 WhatsApp AI Health Chatbot

A production-ready, multilingual WhatsApp chatbot that provides AI-powered health information and guidance using multiple AI services for comprehensive responses.

## ✨ Features

- 🤖 **Multi-AI Integration**: Combines Gemini (reasoning), Perplexity (search), and Groq (summarization)
- 🌍 **Multilingual Support**: Automatic language detection and translation (100+ languages)
- ⚡ **Real-time Responses**: Fast, contextual health information and advice
- 🔍 **Current Information**: Searches latest medical research and health news
- 🚨 **Emergency Detection**: Identifies urgent medical situations
- 📱 **WhatsApp Integration**: Seamless messaging experience
- 📊 **Analytics**: Conversation tracking and user statistics
- 🔒 **Secure**: Environment-based configuration and data protection

## 🏗️ Architecture

```
WhatsApp User → Facebook Webhook → Flask App → AI Services → Response → WhatsApp
                                      ↓
                               SQLite Database
```

### AI Service Flow
1. **Language Detection**: Auto-detect user's language
2. **Translation**: Convert to English for processing (if needed)
3. **Strategy Selection**: Choose response approach based on query type
4. **AI Processing**:
   - **Emergency queries**: Immediate safety response
   - **Search queries**: Perplexity → Gemini → Groq pipeline
   - **General queries**: Gemini → Groq pipeline
5. **Response Generation**: Create helpful, accurate response
6. **Translation**: Convert back to user's language
7. **Delivery**: Send via WhatsApp with medical disclaimer

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Facebook Developer Account
- WhatsApp Business Account
- API keys for Gemini, Groq, and Perplexity

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/whatsapp-health-chatbot.git
cd whatsapp-health-chatbot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
```bash
cp .env.example .env
# Edit .env with your API keys and tokens
```

### 4. Initialize Database
```bash
python -c "from app import init_db; init_db()"
```

### 5. Run Locally
```bash
python app.py
```

### 6. Deploy to Render.com
```bash
# Push to GitHub and connect to Render.com
# Configure environment variables in Render dashboard
# Deploy using render.yaml configuration
```

## 📋 Setup Guides

| Guide | Description |
|-------|-------------|
| 📱 [Complete Setup Guide](setup_guide.md) | Full deployment instructions |
| 📘 [Facebook Developer Setup](facebook_setup_detailed.md) | WhatsApp Business API configuration |
| 🧪 [Testing Guide](testing_guide.md) | Comprehensive testing procedures |

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WHATSAPP_TOKEN` | ✅ | Permanent access token from Facebook |
| `WHATSAPP_PHONE_NUMBER_ID` | ✅ | WhatsApp Business phone number ID |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | ✅ | Business account identifier |
| `VERIFY_TOKEN` | ✅ | Webhook verification token |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `GROQ_API_KEY` | ✅ | Groq API key for text processing |
| `PERPLEXITY_API_KEY` | ✅ | Perplexity search API key |
| `SECRET_KEY` | ✅ | Flask application secret key |

### API Rate Limits

| Service | Free Tier Limit | Notes |
|---------|-----------------|-------|
| WhatsApp Business | 1,000 messages/month | Test numbers only |
| Gemini | 15 RPM, 1.5M tokens/min | Generous free tier |
| Groq | 30 RPM, 6K tokens/min | Fast inference |
| Perplexity | 20 RPM | Real-time search |

## 🎯 Usage Examples

### Basic Health Query
**User**: "I have a headache, what should I do?"

**Bot Response**: 
```
For headaches, try these approaches:

• Stay hydrated - drink plenty of water
• Rest in a quiet, dark room  
• Apply a cold or warm compress
• Consider over-the-counter pain relievers
• Practice relaxation techniques

If headaches persist, worsen, or are accompanied by fever, vision changes, or neck stiffness, consult a healthcare provider.

⚠️ This is not medical advice. Please consult a healthcare professional for medical concerns.
```

### Multilingual Support
**User (Spanish)**: "¿Cuáles son los síntomas de la gripe?"

**Bot Response (Spanish)**:
```
Los síntomas comunes de la gripe incluyen:

• Fiebre y escalofríos
• Dolor de cabeza y muscular
• Tos y dolor de garganta
• Fatiga y debilidad
• Congestión nasal

La gripe generalmente dura 7-10 días. Mantente hidratado, descansa y consulta a un médico si los síntomas empeoran.

⚠️ Esto no es consejo médico. Consulte a un profesional de la salud para problemas médicos.
```

### Emergency Detection
**User**: "Chest pain and trouble breathing"

**Bot Response**:
```
🚨 MEDICAL EMERGENCY DETECTED 🚨

If this is a medical emergency:
• Call your local emergency number immediately (911, 102, etc.)
• Go to the nearest emergency room
• Contact emergency services

I cannot provide emergency medical care. Please seek immediate professional help.
```

## 📊 API Endpoints

### Health Check
```bash
GET /health
```
Returns system status and service availability.

### Webhook
```bash
GET /webhook?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE
POST /webhook
```
WhatsApp webhook for message verification and handling.

### Statistics
```bash
GET /stats
```
Returns conversation analytics and usage statistics.

## 🗄️ Database Schema

### Conversations Table
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_phone TEXT NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    language TEXT DEFAULT 'en',
    ai_service TEXT DEFAULT 'gemini'
);
```

### User Profiles Table
```sql
CREATE TABLE user_profiles (
    phone TEXT PRIMARY KEY,
    name TEXT,
    preferred_language TEXT DEFAULT 'en',
    health_conditions TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 Monitoring

### System Health
- **Health endpoint**: `/health` - Service status
- **Stats endpoint**: `/stats` - Usage analytics
- **Render logs**: Real-time application logs
- **Database queries**: Performance monitoring

### Key Metrics
- Response time (target: < 10 seconds)
- Success rate (target: > 95%)
- Language detection accuracy
- User engagement (messages per user)
- API error rates

## 🛠️ Development

### Project Structure
```
whatsapp-health-chatbot/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render.com configuration
├── gunicorn.conf.py      # Gunicorn settings
├── Dockerfile            # Docker configuration
├── deploy.sh             # Deployment script
├── .env.example          # Environment template
├── runtime.txt           # Python version
├── setup_guide.md        # Setup instructions
├── facebook_setup_detailed.md  # WhatsApp API setup
├── testing_guide.md      # Testing procedures
└── README.md            # This file
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=True

# Run development server
python app.py

# Run tests
python -m pytest tests/
```

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes with tests
3. Update documentation
4. Test thoroughly
5. Submit pull request

## 🔒 Security

### Data Protection
- Environment variables for all secrets
- No sensitive data in logs
- Input validation and sanitization
- SQL injection prevention
- HTTPS-only communication

### Privacy Compliance
- Minimal data collection
- Conversation data encrypted at rest
- User consent mechanisms
- Data retention policies
- GDPR/HIPAA considerations

## 🚦 Troubleshooting

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Bot not responding | Messages sent but no reply | Check webhook URL and API keys |
| Slow responses | > 15 second delays | Optimize AI API calls, upgrade hosting |
| Wrong language | Incorrect translation | Verify Google Translate service |
| API errors | Service unavailable | Check API quotas and rate limits |

### Debug Commands
```bash
# Check logs
render logs --tail --service your-service-name

# Test webhook locally
curl -X GET "http://localhost:5000/webhook?hub.mode=subscribe&hub.verify_token=health_bot_verify_token_2024&hub.challenge=test"

# Verify health
curl https://your-app.onrender.com/health
```

## 📈 Scaling

### Performance Optimization
- Implement Redis for caching
- Use PostgreSQL for better performance
- Add CDN for static assets
- Optimize database queries
- Implement request queuing

### Infrastructure Scaling
- Upgrade Render.com plan
- Implement horizontal scaling
- Add monitoring and alerting
- Set up CI/CD pipeline
- Configure auto-scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for functions
- Write comprehensive tests
- Update documentation

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## 🙋 Support

### Getting Help
- 📖 Read the [Setup Guide](setup_guide.md)
- 🧪 Follow the [Testing Guide](testing_guide.md)
- 📱 Check [Facebook Setup](facebook_setup_detailed.md)
- 🐛 Open an [Issue](https://github.com/yourusername/whatsapp-health-chatbot/issues)

### Commercial Support
For commercial support, custom features, or enterprise deployment, contact [your-email@domain.com].

## 🎉 Acknowledgments

- **Google Gemini** for advanced AI reasoning
- **Groq** for fast text processing
- **Perplexity** for real-time search capabilities
- **Meta** for WhatsApp Business API
- **Render.com** for hosting platform

## 🔮 Roadmap

### Short Term (1-3 months)
- [ ] Voice message support
- [ ] Image analysis capabilities
- [ ] User preference learning
- [ ] Enhanced emergency detection

### Medium Term (3-6 months)
- [ ] Integration with health APIs
- [ ] Appointment scheduling
- [ ] Medication reminders
- [ ] Health tracking features

### Long Term (6+ months)
- [ ] AI model fine-tuning
- [ ] Multi-platform support (Telegram, SMS)
- [ ] Healthcare provider integration
- [ ] Advanced analytics dashboard

---

Made with ❤️ for better healthcare accessibility worldwide.

**⚠️ Important Disclaimer**: This chatbot provides general health information only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult qualified healthcare providers for medical concerns.
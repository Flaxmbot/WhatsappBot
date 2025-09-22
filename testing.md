# Testing & Validation Guide

## 🧪 Complete Testing Checklist for WhatsApp Health Chatbot

### Phase 1: Local Development Testing

#### 1.1 Environment Setup Test
```bash
# Check Python version
python --version  # Should be 3.11+

# Install dependencies
pip install -r requirements.txt

# Check environment variables
python -c "
import os
required = ['WHATSAPP_TOKEN', 'GEMINI_API_KEY', 'GROQ_API_KEY', 'PERPLEXITY_API_KEY']
missing = [var for var in required if not os.getenv(var)]
print('✅ All variables set' if not missing else f'❌ Missing: {missing}')
"
```

#### 1.2 Database Initialization Test
```bash
python -c "
import app
try:
    app.init_db()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

#### 1.3 AI Services Test
```bash
python -c "
import asyncio
from app import get_gemini_response, get_groq_summary, get_perplexity_search

async def test_ai_services():
    try:
        # Test Gemini
        gemini_result = await get_gemini_response('What causes headaches?')
        print('✅ Gemini API working')
        
        # Test Groq
        groq_result = get_groq_summary('This is a long text about headaches and their causes including stress, dehydration, and tension.')
        print('✅ Groq API working')
        
        # Test Perplexity
        perplexity_result = await get_perplexity_search('latest headache treatments')
        print('✅ Perplexity API working' if perplexity_result else '⚠️ Perplexity API issue')
        
    except Exception as e:
        print(f'❌ AI services error: {e}')

asyncio.run(test_ai_services())
"
```

### Phase 2: Flask Application Testing

#### 2.1 Start Local Server
```bash
python app.py
# Should start on http://localhost:5000
```

#### 2.2 Health Check Test
```bash
curl http://localhost:5000/health
# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-XX...",
  "services": {
    "whatsapp": true,
    "gemini": true,
    "groq": true,
    "perplexity": true
  }
}
```

#### 2.3 Webhook Verification Test
```bash
curl -X GET "http://localhost:5000/webhook?hub.mode=subscribe&hub.verify_token=health_bot_verify_token_2024&hub.challenge=test_challenge_123"
# Expected response: test_challenge_123
```

### Phase 3: WhatsApp Integration Testing

#### 3.1 Webhook Registration Test
1. **Start ngrok** (for local testing):
```bash
ngrok http 5000
# Note the HTTPS URL: https://abc123.ngrok.io
```

2. **Register webhook in Facebook Developer Console**:
   - URL: `https://abc123.ngrok.io/webhook`
   - Verify Token: `health_bot_verify_token_2024`

3. **Test webhook verification**:
   - Should show "✅ Webhook verified successfully" in Facebook console

#### 3.2 Message Sending Test
```bash
# Test sending message via WhatsApp API
curl -X POST https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "YOUR_TEST_PHONE_NUMBER",
    "type": "text",
    "text": {
      "body": "Hello! This is a test message from your health bot."
    }
  }'
```

#### 3.3 End-to-End Message Flow Test
1. **Send message to bot**: "I have a headache, what should I do?"
2. **Expected flow**:
   - Webhook receives message ✅
   - Language detected (if non-English) ✅
   - Message translated to English ✅
   - Gemini processes health query ✅
   - Response generated and summarized ✅
   - Response translated back (if needed) ✅
   - Message sent via WhatsApp ✅
   - Conversation saved to database ✅

### Phase 4: Multilingual Testing

#### 4.1 Test Different Languages
**Spanish**: "Tengo dolor de cabeza, ¿qué debo hacer?"
**French**: "J'ai mal à la tête, que dois-je faire?"
**Hindi**: "मुझे सिरदर्द है, मुझे क्या करना चाहिए?"
**Arabic**: "أعاني من صداع، ماذا يجب أن أفعل؟"

#### 4.2 Expected Behavior
- Bot detects language correctly
- Translates to English for processing
- Returns response in original language
- Maintains context and medical disclaimer

### Phase 5: Production Deployment Testing

#### 5.1 Render.com Deployment Test
1. **Check build logs**:
   - Dependencies install successfully
   - No import errors
   - Database initializes

2. **Check runtime logs**:
   - App starts without errors
   - Environment variables loaded
   - All AI services initialized

#### 5.2 Production Health Check
```bash
curl https://your-app.onrender.com/health
# Should return healthy status with all services true
```

#### 5.3 Production Webhook Test
```bash
curl -X GET "https://your-app.onrender.com/webhook?hub.mode=subscribe&hub.verify_token=health_bot_verify_token_2024&hub.challenge=production_test"
# Should return: production_test
```

### Phase 6: Load & Performance Testing

#### 6.1 Concurrent Messages Test
```python
import asyncio
import aiohttp
import json

async def send_test_message(session, message_id):
    webhook_data = {
        "entry": [{
            "changes": [{
                "field": "messages",
                "value": {
                    "messages": [{
                        "from": f"test_user_{message_id}",
                        "type": "text",
                        "text": {"body": f"Test message {message_id}: I have a headache"}
                    }]
                }
            }]
        }]
    }
    
    async with session.post(
        'https://your-app.onrender.com/webhook',
        json=webhook_data,
        headers={'Content-Type': 'application/json'}
    ) as response:
        return await response.text()

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = [send_test_message(session, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        print(f"✅ Processed {len(results)} concurrent messages")

asyncio.run(load_test())
```

#### 6.2 Database Performance Test
```python
import sqlite3
import time

def test_db_performance():
    conn = sqlite3.connect('health_bot.db')
    cursor = conn.cursor()
    
    start_time = time.time()
    
    # Insert test conversations
    for i in range(100):
        cursor.execute('''
            INSERT INTO conversations (user_phone, message, response, language)
            VALUES (?, ?, ?, ?)
        ''', (f'test_user_{i}', f'Test message {i}', f'Test response {i}', 'en'))
    
    conn.commit()
    
    # Query performance test
    cursor.execute('SELECT COUNT(*) FROM conversations')
    count = cursor.fetchone()[0]
    
    end_time = time.time()
    
    print(f"✅ Database performance: {count} records in {end_time - start_time:.2f} seconds")
    
    # Cleanup
    cursor.execute('DELETE FROM conversations WHERE user_phone LIKE "test_user_%"')
    conn.commit()
    conn.close()

test_db_performance()
```

### Phase 7: Error Handling Testing

#### 7.1 API Failure Simulation
```python
# Test with invalid API keys
import os
os.environ['GEMINI_API_KEY'] = 'invalid_key'

# Test bot response - should gracefully handle API errors
```

#### 7.2 Network Failure Test
```python
# Simulate network timeout
import requests
from unittest.mock import patch

def test_network_failure():
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout()
        
        # Test WhatsApp message sending
        result = send_whatsapp_message('test_user', 'test message')
        print('✅ Handles network timeout gracefully' if not result else '❌ Error handling failed')
```

### Phase 8: Security Testing

#### 8.1 Input Validation Test
```python
# Test malicious inputs
malicious_inputs = [
    "'; DROP TABLE conversations; --",
    "<script>alert('xss')</script>",
    "../../etc/passwd",
    "{{7*7}}",  # Template injection
    "A" * 10000  # Very long input
]

for malicious_input in malicious_inputs:
    # Test that bot handles malicious input safely
    print(f"Testing: {malicious_input[:50]}...")
    # Should not crash or execute malicious code
```

#### 8.2 Environment Variables Security Test
```bash
# Check that sensitive data is not logged
grep -r "WHATSAPP_TOKEN\|API_KEY" logs/ 
# Should return no results
```

### Phase 9: User Experience Testing

#### 9.1 Response Quality Test
Test with various health queries:

**General Health**: "How can I improve my immune system?"
**Specific Symptoms**: "I have chest pain and shortness of breath"
**Medication**: "What are the side effects of aspirin?"
**Emergency**: "I think I'm having a heart attack"
**Wellness**: "Best exercises for back pain"

#### 9.2 Response Time Test
```python
import time
start_time = time.time()
# Send message to bot
end_time = time.time()
response_time = end_time - start_time
print(f"Response time: {response_time:.2f} seconds")
# Should be < 10 seconds for good UX
```

### Phase 10: Monitoring & Analytics Testing

#### 10.1 Stats Endpoint Test
```bash
curl https://your-app.onrender.com/stats
# Expected response:
{
  "total_conversations": 150,
  "unique_users": 45,
  "language_distribution": {"en": 100, "es": 30, "fr": 20},
  "timestamp": "2024-01-..."
}
```

#### 10.2 Database Query Test
```sql
-- Most active users
SELECT user_phone, COUNT(*) as message_count 
FROM conversations 
GROUP BY user_phone 
ORDER BY message_count DESC 
LIMIT 10;

-- Language distribution
SELECT language, COUNT(*) as count 
FROM conversations 
GROUP BY language;

-- Hourly message volume
SELECT strftime('%H', timestamp) as hour, COUNT(*) as messages
FROM conversations 
GROUP BY hour 
ORDER BY hour;
```

## 🎯 Testing Checklist Summary

### ✅ Pre-Deployment Checklist
- [ ] All environment variables configured
- [ ] Dependencies install without errors
- [ ] Database initializes successfully
- [ ] All AI APIs respond correctly
- [ ] Local Flask app starts and responds
- [ ] Webhook verification works
- [ ] Message sending functionality works

### ✅ Post-Deployment Checklist
- [ ] Production health check passes
- [ ] Webhook receives messages from WhatsApp
- [ ] End-to-end message flow works
- [ ] Multiple languages supported
- [ ] Error handling works gracefully
- [ ] Response times are acceptable (< 10 seconds)
- [ ] Database operations perform well
- [ ] Stats endpoint returns correct data
- [ ] Security measures prevent malicious input
- [ ] All AI services integrate properly

### ✅ Ongoing Monitoring Checklist
- [ ] Daily health check monitoring
- [ ] Weekly conversation volume review
- [ ] Monthly API usage analysis
- [ ] Quarterly user feedback assessment
- [ ] Semi-annual security audit

## 🚨 Common Issues & Solutions

### Issue: Bot Not Responding to Messages

**Symptoms**:
- Messages appear in WhatsApp but bot doesn't respond
- Webhook receives data but no processing occurs

**Debugging Steps**:
```bash
# Check Render logs
render logs --tail --service your-service-name

# Test webhook locally
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"entry":[{"changes":[{"field":"messages","value":{"messages":[{"from":"test","type":"text","text":{"body":"test message"}}]}}]}]}'
```

**Common Solutions**:
1. Check environment variables are set correctly
2. Verify AI API keys are valid and have quota
3. Check database connection
4. Ensure webhook URL is accessible

### Issue: Slow Response Times

**Symptoms**:
- Bot takes > 15 seconds to respond
- Users complain about delays

**Debugging**:
```python
import time
import logging

# Add timing logs to your functions
def timed_function(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logging.info(f"{func.__name__} took {end-start:.2f} seconds")
        return result
    return wrapper
```

**Solutions**:
1. Optimize AI API calls (reduce token limits)
2. Implement caching for common queries
3. Use async processing for non-critical operations
4. Upgrade Render.com plan for better performance

### Issue: Language Translation Errors

**Symptoms**:
- Bot responds in wrong language
- Translation quality is poor

**Testing**:
```python
from googletrans import Translator
translator = Translator()

test_phrases = [
    ("Hello, I have a headache", "es"),
    ("¿Cómo estás?", "en"),
    ("J'ai mal à la tête", "en")
]

for phrase, target_lang in test_phrases:
    result = translator.translate(phrase, dest=target_lang)
    print(f"'{phrase}' -> '{result.text}' (confidence: {result.confidence})")
```

**Solutions**:
1. Check Google Translate API quota
2. Implement fallback to English if translation fails
3. Add language confidence threshold
4. Cache common translations

### Issue: WhatsApp API Rate Limiting

**Symptoms**:
- Messages fail to send
- API returns 429 status code

**Monitoring**:
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=20, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def can_make_request(self):
        now = time.time()
        # Remove old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        return len(self.requests) < self.max_requests
    
    def make_request(self):
        if self.can_make_request():
            self.requests.append(time.time())
            return True
        return False

# Usage
rate_limiter = RateLimiter(max_requests=20, time_window=60)
```

**Solutions**:
1. Implement exponential backoff
2. Queue messages during high traffic
3. Upgrade to business verified account
4. Optimize message content to reduce API calls

## 📊 Performance Benchmarks

### Expected Response Times
- **Simple health query**: 2-5 seconds
- **Complex query with search**: 5-10 seconds
- **Multilingual query**: 3-7 seconds
- **Emergency detection**: < 2 seconds

### API Rate Limits
- **WhatsApp Business**: 1,000 messages/second (verified)
- **Gemini**: 15 requests/minute (free tier)
- **Groq**: 30 requests/minute (free tier)
- **Perplexity**: 20 requests/minute (free tier)

### Database Performance
- **Insert conversation**: < 100ms
- **Query user stats**: < 200ms
- **Language distribution**: < 500ms
- **Complex analytics**: < 2 seconds

## 🔧 Advanced Testing Scripts

### Comprehensive Load Test
```python
import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime

class ChatbotLoadTester:
    def __init__(self, base_url, webhook_endpoint="/webhook"):
        self.base_url = base_url
        self.webhook_endpoint = webhook_endpoint
        self.test_messages = [
            "I have a headache, what should I do?",
            "¿Cuáles son los síntomas de la gripe?",
            "J'ai mal au dos, que faire?",
            "What are the benefits of exercise?",
            "How can I improve my sleep?",
            "मुझे पेट में दर्द है",
            "Latest research on vitamin D",
            "Emergency: chest pain and breathing difficulty"
        ]
    
    async def send_message(self, session, user_id, message):
        webhook_data = {
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "from": f"load_test_user_{user_id}",
                            "type": "text",
                            "text": {"body": message},
                            "timestamp": str(int(time.time()))
                        }]
                    }
                }]
            }]
        }
        
        start_time = time.time()
        try:
            async with session.post(
                f"{self.base_url}{self.webhook_endpoint}",
                json=webhook_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                return {
                    "user_id": user_id,
                    "message": message,
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                "user_id": user_id,
                "message": message,
                "error": str(e),
                "response_time": end_time - start_time,
                "success": False
            }
    
    async def run_load_test(self, concurrent_users=10, messages_per_user=5):
        print(f"🚀 Starting load test: {concurrent_users} users, {messages_per_user} messages each")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for user_id in range(concurrent_users):
                for msg_num in range(messages_per_user):
                    message = random.choice(self.test_messages)
                    tasks.append(self.send_message(session, user_id, message))
                    
                    # Stagger requests slightly
                    await asyncio.sleep(0.1)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results
            successful = [r for r in results if isinstance(r, dict) and r.get('success', False)]
            failed = [r for r in results if isinstance(r, dict) and not r.get('success', True)]
            errors = [r for r in results if isinstance(r, Exception)]
            
            print(f"\n📊 Load Test Results:")
            print(f"  ✅ Successful: {len(successful)}")
            print(f"  ❌ Failed: {len(failed)}")
            print(f"  💥 Errors: {len(errors)}")
            
            if successful:
                response_times = [r['response_time'] for r in successful]
                print(f"  ⏱️  Average response time: {sum(response_times)/len(response_times):.2f}s")
                print(f"  ⏱️  Max response time: {max(response_times):.2f}s")
                print(f"  ⏱️  Min response time: {min(response_times):.2f}s")
            
            return results

# Run load test
async def main():
    tester = ChatbotLoadTester("https://your-app.onrender.com")
    await tester.run_load_test(concurrent_users=5, messages_per_user=3)

if __name__ == "__main__":
    asyncio.run(main())
```

### Database Stress Test
```python
import sqlite3
import threading
import time
import random

def database_stress_test(num_threads=5, operations_per_thread=100):
    print(f"🗄️  Database stress test: {num_threads} threads, {operations_per_thread} operations each")
    
    def worker(thread_id):
        conn = sqlite3.connect('health_bot.db')
        cursor = conn.cursor()
        
        for i in range(operations_per_thread):
            try:
                # Random operations
                operation = random.choice(['insert', 'select', 'update'])
                
                if operation == 'insert':
                    cursor.execute('''
                        INSERT INTO conversations (user_phone, message, response, language)
                        VALUES (?, ?, ?, ?)
                    ''', (f'stress_test_{thread_id}_{i}', f'Test message {i}', f'Test response {i}', 'en'))
                
                elif operation == 'select':
                    cursor.execute('SELECT COUNT(*) FROM conversations WHERE user_phone LIKE ?', (f'stress_test_{thread_id}%',))
                    cursor.fetchone()
                
                elif operation == 'update':
                    cursor.execute('''
                        UPDATE user_profiles SET last_active = ? WHERE phone = ?
                    ''', (time.time(), f'stress_test_{thread_id}'))
                
                conn.commit()
                
            except Exception as e:
                print(f"❌ Thread {thread_id}, operation {i}: {e}")
        
        # Cleanup
        cursor.execute('DELETE FROM conversations WHERE user_phone LIKE ?', (f'stress_test_{thread_id}%',))
        conn.commit()
        conn.close()
        print(f"✅ Thread {thread_id} completed")
    
    start_time = time.time()
    
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_operations = num_threads * operations_per_thread
    print(f"📊 Database stress test completed:")
    print(f"  Total operations: {total_operations}")
    print(f"  Total time: {end_time - start_time:.2f} seconds")
    print(f"  Operations per second: {total_operations / (end_time - start_time):.2f}")

# Run stress test
database_stress_test(num_threads=3, operations_per_thread=50)
```

### API Integration Test Suite
```python
import asyncio
import os
from datetime import datetime

class APITestSuite:
    def __init__(self):
        self.results = {}
    
    async def test_gemini_api(self):
        print("🧠 Testing Gemini API...")
        try:
            from app import get_gemini_response
            result = await get_gemini_response("What causes common cold?")
            self.results['gemini'] = {
                'status': 'success' if result else 'failure',
                'response_length': len(result) if result else 0,
                'contains_disclaimer': 'not medical advice' in result.lower() if result else False
            }
            print(f"  ✅ Gemini API: {len(result)} characters")
        except Exception as e:
            self.results['gemini'] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ Gemini API error: {e}")
    
    async def test_groq_api(self):
        print("⚡ Testing Groq API...")
        try:
            from app import get_groq_summary
            long_text = "This is a very long health-related text about symptoms, treatments, and medical advice that needs to be summarized into a shorter, more concise format for better user experience. It contains multiple sentences and detailed information."
            result = get_groq_summary(long_text)
            self.results['groq'] = {
                'status': 'success' if result else 'failure',
                'response_length': len(result) if result else 0,
                'is_shorter': len(result) < len(long_text) if result else False
            }
            print(f"  ✅ Groq API: Summarized {len(long_text)} → {len(result)} characters")
        except Exception as e:
            self.results['groq'] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ Groq API error: {e}")
    
    async def test_perplexity_api(self):
        print("🔍 Testing Perplexity API...")
        try:
            from app import get_perplexity_search
            result = await get_perplexity_search("latest COVID-19 treatments")
            self.results['perplexity'] = {
                'status': 'success' if result else 'failure',
                'response_length': len(result) if result else 0,
                'has_sources': 'source' in result.lower() if result else False
            }
            print(f"  ✅ Perplexity API: {len(result)} characters" if result else "  ⚠️ Perplexity API: No response")
        except Exception as e:
            self.results['perplexity'] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ Perplexity API error: {e}")
    
    async def test_translation_service(self):
        print("🌍 Testing Translation Service...")
        try:
            from app import translate_text, detect_language
            
            # Test detection
            spanish_text = "Hola, ¿cómo estás?"
            detected_lang = detect_language(spanish_text)
            
            # Test translation
            translated = translate_text(spanish_text, 'en', 'es')
            
            self.results['translation'] = {
                'status': 'success',
                'language_detected': detected_lang,
                'translation_works': len(translated) > 0,
                'original_length': len(spanish_text),
                'translated_length': len(translated)
            }
            print(f"  ✅ Translation: '{spanish_text}' → '{translated}'")
        except Exception as e:
            self.results['translation'] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ Translation error: {e}")
    
    async def run_all_tests(self):
        print("🧪 Running API Integration Test Suite\n")
        
        await asyncio.gather(
            self.test_gemini_api(),
            self.test_groq_api(),
            self.test_perplexity_api(),
            self.test_translation_service()
        )
        
        print("\n📊 Test Results Summary:")
        for service, result in self.results.items():
            status = result.get('status', 'unknown')
            emoji = "✅" if status == 'success' else "❌" if status == 'error' else "⚠️"
            print(f"  {emoji} {service.capitalize()}: {status}")
            
            if 'error' in result:
                print(f"    Error: {result['error']}")
        
        # Overall health check
        successful_services = sum(1 for r in self.results.values() if r.get('status') == 'success')
        total_services = len(self.results)
        health_percentage = (successful_services / total_services) * 100
        
        print(f"\n🎯 Overall System Health: {health_percentage:.1f}% ({successful_services}/{total_services} services)")
        
        return self.results

# Run API tests
async def main():
    test_suite = APITestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📋 Final Production Checklist

### Before Going Live
- [ ] All API keys configured and tested
- [ ] WhatsApp Business Account verified
- [ ] Permanent access token obtained
- [ ] Webhook URL updated to production
- [ ] Database optimized and backed up
- [ ] Error handling tested thoroughly
- [ ] Load testing completed successfully
- [ ] Security audit performed
- [ ] Privacy policy published
- [ ] Terms of service created
- [ ] User documentation prepared

### Launch Day
- [ ] Monitor system health continuously
- [ ] Watch for webhook delivery issues
- [ ] Check API rate limits and quotas
- [ ] Monitor response times
- [ ] Track user engagement metrics
- [ ] Be ready for quick fixes
- [ ] Have rollback plan prepared

### Post-Launch (Week 1)
- [ ] Daily health checks
- [ ] User feedback collection
- [ ] Performance optimization
- [ ] Bug fixes and improvements
- [ ] Documentation updates
- [ ] Team training on monitoring tools

Your WhatsApp AI Health Chatbot is now thoroughly tested and ready for production! 🎉
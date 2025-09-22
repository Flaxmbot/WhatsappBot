# Facebook WhatsApp Business API - Detailed Setup Guide

## 🔐 Getting Permanent Access Tokens & Production Setup

### Part 1: Facebook Developer Console Setup

#### Step 1: Create Facebook Developer Account
1. **URL**: Go to https://developers.facebook.com/
2. **Click**: "Get Started" button (top right)
3. **Login**: Use your Facebook account or create new one
4. **Verify**: Complete phone number and email verification
5. **Accept**: Developer terms and conditions

#### Step 2: Create New App
1. **Dashboard**: Click "Create App" button
2. **Use Case**: Select "Business" → Continue
3. **App Details**:
   - **Display Name**: `Health AI Chatbot`
   - **App Contact Email**: your-email@domain.com
   - **Business Account**: Select existing or create new
4. **Click**: "Create App" button
5. **App ID**: Note down your App ID (you'll need this)

#### Step 3: Add WhatsApp Business Product
1. **Products**: In left sidebar, find "Add Products to Your App"
2. **WhatsApp**: Find "WhatsApp" tile and click "Set up"
3. **API Setup**: You'll be redirected to WhatsApp API Setup page

### Part 2: WhatsApp Business API Configuration

#### Step 4: Initial API Setup
In the WhatsApp > Getting Started section, you'll see:

**Test Phone Number (Provided by Meta)**
- Number: +1 555-0199 (example)
- Phone Number ID: `120363300490243511` (copy this)

**Temporary Access Token**
- Token: `EAALxK7...` (24 hours validity)
- Copy this token for initial testing

**Business Account ID**
- ID: `123456789012345` (copy this)

#### Step 5: Configure Webhook
1. **Navigate**: WhatsApp > Configuration > Webhook
2. **Callback URL**: `https://your-render-app.onrender.com/webhook`
3. **Verify Token**: `health_bot_verify_token_2024`
4. **Click**: "Verify and Save"
5. **Webhook Fields**: Subscribe to:
   - ✅ messages
   - ✅ message_deliveries
   - ✅ message_echoes (optional)

### Part 3: Getting Permanent Access Token

#### Option A: Business Verification Method (Recommended)

**Step 6A: Start Business Verification**
1. **Navigate**: Meta Business Suite (business.facebook.com)
2. **Settings**: Business Settings → Security Center
3. **Get Verified**: Click "Start Verification"

**Required Documents**:
- Business license or registration certificate
- Utility bill or bank statement (business address)
- Government-issued ID of business owner
- Tax registration documents

**Step 7A: Complete Verification Process**
1. **Upload Documents**: Submit all required documents
2. **Business Details**: 
   - Legal business name
   - Business address
   - Phone number
   - Website (optional)
   - Business category: "Healthcare & Medical"
3. **Review Time**: 1-3 business days
4. **Status**: Check verification status in Business Settings

**Step 8A: Generate Permanent Token (After Verification)**
1. **WhatsApp Manager**: business.facebook.com/wa/manage
2. **API Setup**: Select your phone number
3. **Generate Token**: Click "Generate Token"
4. **Permissions**: Select:
   - ✅ whatsapp_business_messaging
   - ✅ whatsapp_business_management
5. **Token**: Copy the permanent token (never expires)

#### Option B: System User Method (Alternative)

**Step 6B: Create System User**
1. **Navigate**: Business Settings → Users → System Users
2. **Add**: Click "Add" button
3. **Details**:
   - **Name**: `Health Bot System User`
   - **Role**: Select "Admin"
4. **Create**: Click "Create System User"

**Step 7B: Generate System User Token**
1. **Select User**: Click on created system user
2. **Generate Token**: Click "Generate New Token"
3. **App**: Select your Health Chatbot app
4. **Permissions**: Grant:
   - ✅ whatsapp_business_messaging
   - ✅ whatsapp_business_management
   - ✅ business_management
5. **Generate**: Click "Generate Token"
6. **Copy Token**: This token never expires

### Part 4: Production Phone Number Setup

#### Step 8: Add Your Business Phone Number
1. **WhatsApp Manager**: business.facebook.com/wa/manage
2. **Phone Numbers**: Click "Add Phone Number"
3. **Verification Methods**:
   - **SMS**: Receive verification code via SMS
   - **Voice Call**: Receive code via phone call
4. **Enter Number**: Your business phone number
5. **Verify**: Enter the 6-digit code received
6. **Display Name**: Set public business name
7. **Category**: Select "Health & Medical"

#### Step 9: Get Production Phone Number ID
1. **API Setup**: Go to developers.facebook.com → Your App → WhatsApp → API Setup
2. **Phone Numbers**: You'll now see your verified number
3. **Phone Number ID**: Copy the new Phone Number ID
4. **Update**: Replace test Phone Number ID in your environment variables

### Part 5: App Review for Production

#### Step 10: Submit App for Review (For Higher Limits)
1. **App Review**: developers.facebook.com → Your App → App Review
2. **Permissions**: Request these permissions:
   - `whatsapp_business_messaging` (Standard)
   - `whatsapp_business_management` (Advanced)
3. **Use Case**: Select "Customer Support/Service"
4. **Description**: 
   ```
   AI-powered health information chatbot that provides:
   - General health guidance and wellness tips
   - Health information search and research
   - Multilingual health support
   - Always disclaims medical advice and encourages professional consultation
   ```
5. **Demo Video**: Create 2-3 minute video showing:
   - User sending health question
   - Bot responding with helpful information
   - Disclaimer about professional medical advice
6. **Privacy Policy**: Provide URL to your privacy policy
7. **Submit**: Click "Submit for Review"

### Part 6: Environment Variables Summary

After completing setup, your `.env` file should have:

```bash
# From WhatsApp API Setup page
WHATSAPP_TOKEN=EAALxK7xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=120363300490243511
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789012345

# Your webhook verify token
VERIFY_TOKEN=health_bot_verify_token_2024

# API Keys (get from respective platforms)
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# App configuration
SECRET_KEY=your-super-secret-key-change-this
```

### Part 7: Rate Limits & Quotas

#### Test Phone Number Limits
- **Messages**: 1,000 messages per month
- **Recipients**: 5 phone numbers max
- **Rate**: 20 messages per minute

#### Business Verified Limits
- **Messages**: Unlimited (pay per message after free tier)
- **Recipients**: Unlimited
- **Rate**: 1,000 messages per second

#### Conversation Pricing (After Free Tier)
- **Service Conversations**: $0.005 per conversation
- **Marketing Conversations**: $0.01 - $0.15 per conversation (varies by country)
- **Free Tier**: 1,000 service conversations per month

### Part 8: Testing & Validation

#### Webhook Test
```bash
curl -X GET "https://your-app.onrender.com/webhook?hub.mode=subscribe&hub.verify_token=health_bot_verify_token_2024&hub.challenge=test_challenge"
# Should return: test_challenge
```

#### Send Test Message
```bash
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

### Part 9: Monitoring & Maintenance

#### WhatsApp Manager Dashboard
- **URL**: business.facebook.com/wa/manage
- **Monitor**: 
  - Message delivery rates
  - Conversation volumes
  - Quality ratings
  - Account status

#### Important URLs to Bookmark
- **Developer Console**: developers.facebook.com/apps/your-app-id
- **WhatsApp Manager**: business.facebook.com/wa/manage
- **Business Settings**: business.facebook.com/settings
- **API Documentation**: developers.facebook.com/docs/whatsapp

### Part 10: Troubleshooting Common Issues

#### Issue: Webhook Not Receiving Messages
**Solution**:
1. Check webhook URL is HTTPS and accessible
2. Verify webhook token matches exactly
3. Check subscribed webhook fields include "messages"
4. Test webhook verification endpoint manually

#### Issue: Access Token Expired
**Solution**:
1. If using temporary token, get permanent token via business verification
2. Generate new system user token
3. Update environment variables immediately

#### Issue: Phone Number Not Verified
**Solution**:
1. Ensure phone number can receive SMS/calls
2. Try different verification method
3. Contact Facebook Business Support if stuck

#### Issue: Messages Not Sending
**Solution**:
1. Check phone number is registered with WhatsApp
2. Verify recipient phone number format (+country_code)
3. Check API rate limits
4. Validate access token permissions

### Part 11: Security Best Practices

#### Token Security
- Never commit tokens to version control
- Use environment variables for all secrets
- Rotate tokens periodically
- Monitor token usage in Facebook Developer Console

#### Webhook Security
- Verify webhook signatures (implement in production)
- Use HTTPS only
- Validate all incoming data
- Rate limit webhook endpoints

#### Data Privacy
- Don't store sensitive health information
- Implement data retention policies
- Comply with HIPAA/GDPR if applicable
- Provide clear privacy policy

This completes your Facebook WhatsApp Business API setup! Your bot should now be ready for production use with permanent tokens and proper webhook configuration.
# AI MARKETER JAR 🎯

A secure, commercial-grade marketing automation platform with natural language interface. Built for marketers to manage campaigns across GoHighLevel, Google Ads, Facebook/Instagram Ads, and Twilio SMS - all through simple conversational commands.

## Key Features

### 🔐 Three-Layer Memory Architecture
- **L1 Working Memory**: Temporary session data and active workflows
- **L2 Session Memory**: Campaign history, analytics, and persistent data
- **L3 Encrypted Memory**: Secure credential storage with military-grade encryption

### 🚀 Marketing Platform Integrations
- **GoHighLevel CRM**: Contact management, pipelines, campaigns
- **Google Ads**: Search & display campaigns, keyword management, optimization
- **Facebook/Instagram Ads**: Social media advertising, audience targeting
- **Twilio SMS**: Bulk messaging, templates, campaign broadcasts

### 🛡️ Security Features
- Encrypted credential storage that customers cannot access
- No system file access or command execution
- Secure MCP interface with marketing-only tools
- Audit logging for all credential access

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download the AI MARKETER JAR directory

2. Navigate to the directory:
```bash
cd ai_marketer_jar
```

3. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create data directory:
```bash
mkdir -p data
```

## Configuration

### Setting Up Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "ai-marketer-jar": {
      "command": "python",
      "args": ["/path/to/ai_marketer_jar/mcp_marketing_server.py"],
      "cwd": "/path/to/ai_marketer_jar"
    }
  }
}
```

### Running Standalone

```bash
python mcp_marketing_server.py
```

## Usage Examples

### Natural Language Commands

Once connected through Claude MCP, you can use natural language commands:

#### Setting Up Credentials
```
"Setup my GoHighLevel API key ABC123 for location XYZ"
"Configure Google Ads with developer token DEV123"
"Add my Twilio credentials with account SID and auth token"
```

#### Campaign Management
```
"Create a Google Ads campaign called Summer Sale with $100 daily budget"
"Pause my Facebook campaign"
"List all active campaigns"
"Get performance metrics for the last 7 days"
```

#### SMS Marketing
```
"Send SMS 'Special offer today!' to +1234567890"
"Broadcast message to my VIP customer list"
"Create SMS template for appointment reminders"
```

#### CRM Operations
```
"Create contact John Doe with email john@example.com"
"Add tag 'hot-lead' to contact"
"Create pipeline for Q1 sales"
```

## API Credentials Required

### GoHighLevel
- API Key
- Location ID (optional)

### Google Ads
- Developer Token
- Client ID
- Client Secret
- Refresh Token
- Customer ID

### Facebook Ads
- Access Token
- Ad Account ID
- App ID (optional)
- App Secret (optional)

### Twilio
- Account SID
- Auth Token
- From Phone Number

## Security Notice

- All API credentials are encrypted using Fernet symmetric encryption
- Credentials are stored in L3 memory with restricted file permissions
- The MCP interface cannot read or expose stored credentials
- All credential access is logged for audit purposes

## Architecture

```
ai_marketer_jar/
├── brain.py                    # Three-layer memory system
├── mcp_marketing_server.py     # MCP server interface
├── controllers/
│   ├── ghl_controller.py       # GoHighLevel integration
│   ├── google_ads_controller.py # Google Ads integration
│   ├── facebook_ads_controller.py # Facebook Ads integration
│   └── twilio_controller.py    # Twilio SMS integration
├── data/                        # Data storage directory
│   ├── l2_session.db           # Session memory database
│   ├── l3_secure.db            # Encrypted credentials
│   └── .encryption_key         # Encryption key (auto-generated)
└── requirements.txt            # Python dependencies
```

## Available MCP Tools

- `setup_credentials`: Configure API credentials for any platform
- `marketing_command`: Execute natural language marketing commands
- `create_campaign`: Create campaigns on any platform
- `list_campaigns`: List all campaigns
- `send_sms`: Send individual SMS messages
- `broadcast_sms`: Send bulk SMS campaigns
- `get_metrics`: Retrieve performance metrics
- `manage_contacts`: Add/remove/list contacts
- `get_memory_stats`: View memory usage statistics
- `get_campaign_history`: Access campaign history

## Support

This is a commercial product. For support, licensing, or custom integrations, contact your vendor.

## License

Proprietary software. All rights reserved.

---

**Note**: This product is designed for legitimate marketing purposes only. Users are responsible for compliance with all applicable laws and regulations including CAN-SPAM, GDPR, and platform-specific terms of service.
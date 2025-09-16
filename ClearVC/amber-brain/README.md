# ClearVC Amber Brain 🧠

Intelligent call orchestration system for after-hours customer service, powered by AI and integrated with Retell and GoHighLevel.

## Overview

Amber Brain is an intelligent orchestrator that:
- Handles after-hours calls through Retell AI
- Identifies and categorizes callers using GHL CRM data
- Provides contextual, intelligent responses
- Creates follow-ups and updates CRM automatically
- Escalates urgent issues to human agents

## Architecture

```
Retell (Voice) → Amber Brain (Intelligence) → GHL (CRM/Actions)
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Retell AI account
- GoHighLevel account
- OpenAI API key

### Local Development

1. Clone and setup:
```bash
cd ClearVC/amber-brain
cp .env.example .env
# Edit .env with your credentials
```

2. Deploy locally:
```bash
./deploy.sh
```

3. Check health:
```bash
curl http://localhost:8000/health
```

## Configuration

Edit `.env` file with your credentials:

```env
# Retell
RETELL_API_KEY=your_key_here

# GoHighLevel
GHL_API_KEY=your_key_here
GHL_LOCATION_ID=your_location_id

# OpenAI
OPENAI_API_KEY=your_key_here

# Notifications (optional)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Webhook URLs

Configure these in Retell:

- **Call Start**: `https://your-domain.com/webhooks/retell/call-started`
- **Call End**: `https://your-domain.com/webhooks/retell/call-ended`
- **Transcript**: `https://your-domain.com/webhooks/retell/transcript-update`
- **Tool Call**: `https://your-domain.com/webhooks/retell/tool-call`

## Deployment

### Railway

1. Push to GitHub
2. Connect repo to Railway
3. Set environment variables in Railway dashboard
4. Deploy

### Docker (Production)

```bash
docker-compose -f docker-compose.yml up -d
```

## API Endpoints

- `GET /health` - Health check
- `GET /calls` - List recent calls
- `GET /calls/{call_id}` - Get call details
- `GET /contacts/{phone}` - Get contact info
- `POST /brain/train` - Train brain with new patterns

## Caller Types

The brain categorizes callers as:
- **VIP** - High-value clients
- **Existing Issue** - Has open support ticket
- **Active Opportunity** - In sales pipeline
- **Past Client** - Previous customer
- **New** - Unknown caller

## Features

### Intelligent Context
- Pulls full contact history from GHL
- Generates dynamic conversation strategies
- Adapts tone and approach based on caller type

### Real-time Processing
- Live transcript analysis
- Sentiment detection
- Automatic escalation for urgent issues

### Automation
- Creates follow-up tasks
- Updates CRM records
- Sends summary notifications
- Books appointments

## Monitoring

View logs:
```bash
docker-compose logs -f amber-brain
```

Check status:
```bash
docker-compose ps
```

## Troubleshooting

### Services won't start
```bash
docker-compose down -v
./deploy.sh clean
./deploy.sh
```

### Database issues
```bash
docker-compose exec postgres psql -U clearvc -d clearvc_brain
```

### API not responding
Check logs for errors:
```bash
docker-compose logs amber-brain | grep ERROR
```

## Development

### Add new tool
1. Add handler in `brain.py`
2. Map in `webhooks.py`
3. Test with Retell

### Modify AI behavior
Edit prompts in `ai_engine.py`

### Database migrations
```bash
docker-compose exec amber-brain alembic upgrade head
```

## Support

For issues or questions, contact the development team.

## License

Proprietary - ClearVC
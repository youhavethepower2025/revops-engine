# Voice Agent Real-Time Implementation Instructions

## Context Overview

You are building a real-time voice agent that handles live phone calls. This is different from the Ambient AI pipeline that already exists in Spectrum, which processes recordings AFTER calls are complete.

## What Already Exists in Spectrum Server

In the `/app` directory of the Spectrum server, you have:

1. **Twilio Controller** at `/app/twilio_controller.py`
   - Contains Twilio account credentials
   - Has 8 phone numbers ready to use
   - Basic SMS and call initiation methods
   - Account SID: [REDACTED]

2. **Ambient AI Pipeline** at `/app/ambient-ai/`
   - Complete Cloudflare Workers implementation
   - Processes recordings AFTER calls end
   - Extracts intelligence, creates embeddings, stores in database
   - Uses Cloudflare Whisper for transcription
   - Uses Qwen for intelligence extraction
   - This is for POST-CALL processing, not real-time

3. **Database** at `/app/brain.db`
   - SQLite database with memories and configurations
   - Contains API keys and tokens in unified_memory table

4. **API Tokens Available**
   - Cloudflare API Token: TyCmFLgySVRZ5RFOvoXXq9gOKbl3HNHaXCp7YIKc
   - Railway API Token: 947a7807-272c-4cd7-8887-9127e92c4964
   - GHL credentials for webhook integration

## What You Need to Build

Create a NEW real-time voice agent that:

1. **Handles incoming calls in real-time** - not recordings after the fact
2. **Uses Twilio Media Streams WebSocket** - for bidirectional audio streaming during the call
3. **Processes audio in real-time** - converts speech to text AS the person speaks
4. **Generates responses immediately** - uses LLM to respond in the conversation
5. **Converts responses to speech** - and streams back to the caller
6. **Sends data to GHL after call** - full transcript and metadata via webhook

## Architecture Requirements

### The Flow

When someone calls a Twilio number:
1. Twilio hits your webhook endpoint with call details
2. You respond with TwiML that includes a Stream directive
3. Twilio opens a WebSocket connection to your media-stream endpoint
4. Audio flows bidirectionally through this WebSocket
5. You process audio chunks in real-time
6. After call ends, send transcript to GHL

### Technology Stack to Use

- **Deployment Target**: Railway (use the Railway API token from Spectrum)
- **Framework**: FastAPI with WebSocket support
- **Speech-to-Text**: Cloudflare Workers AI Whisper model (free tier)
- **LLM for Responses**: Cloudflare Workers AI Llama or Mistral model (free tier)
- **Text-to-Speech**: ElevenLabs API (for voice selection capabilities)
- **Database**: PostgreSQL on Railway for conversation storage
- **Post-Call Webhook**: Send to GHL using their API

### File Structure to Create

```
voice-agent/
├── main.py                 # FastAPI application with WebSocket handler
├── requirements.txt        # Python dependencies
├── railway.toml           # Railway configuration
├── audio_processor.py     # Handles audio streaming and buffering
├── cloudflare_ai.py       # Interface to Cloudflare Workers AI
├── elevenlabs_tts.py      # ElevenLabs text-to-speech
├── ghl_webhook.py         # Sends data to GHL after calls
└── .env                   # Environment variables
```

## Implementation Details

### WebSocket Connection

The WebSocket needs to handle Twilio's specific message format. Twilio sends JSON messages with events like:
- `start` - Connection initiated, includes metadata
- `media` - Audio chunk in base64 mulaw format
- `stop` - Call ended

You need to:
- Decode the mulaw audio to PCM
- Buffer audio chunks until you have enough for STT
- Send audio back in the same mulaw format

### Real-Time Processing Pipeline

1. **Audio Buffering**: Collect 0.5-1 second of audio before processing
2. **STT Processing**: Send buffer to Cloudflare Whisper
3. **Context Management**: Keep conversation history in memory
4. **Response Generation**: Use Cloudflare LLM with conversation context
5. **TTS Generation**: Convert response to audio with ElevenLabs
6. **Audio Streaming**: Send audio back through WebSocket

### Cloudflare Workers AI Integration

Use the Cloudflare API directly from Python:
- Endpoint: `https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/openai/whisper`
- Use the Cloudflare token from Spectrum
- Account ID: bbd9ec5819a97651cc9f481c1c275c3d

### GHL Integration

After each call:
- Create or update contact with phone number
- Add conversation transcript as a note
- Tag the contact appropriately
- Use the GHL API key: pit-fdf8bee7-9c21-4748-b265-e732781c8b3f

## Critical Implementation Notes

1. **Do NOT use third-party WebRTC services** - use direct Twilio Media Streams
2. **Do NOT use OpenAI APIs** - use Cloudflare Workers AI for all inference
3. **Do NOT create a basic webhook handler** - implement full bidirectional streaming
4. **Do NOT store audio files** - process in memory and only save transcripts
5. **Do NOT block on API calls** - use async processing throughout

## Environment Variables Needed

```
RAILWAY_TOKEN=947a7807-272c-4cd7-8887-9127e92c4964
CLOUDFLARE_API_TOKEN=TyCmFLgySVRZ5RFOvoXXq9gOKbl3HNHaXCp7YIKc
CLOUDFLARE_ACCOUNT_ID=bbd9ec5819a97651cc9f481c1c275c3d
TWILIO_ACCOUNT_SID=[REDACTED]
TWILIO_AUTH_TOKEN=e65397c32f16f83469ee9d859308eb6a
ELEVENLABS_API_KEY=(get from user or use free tier)
GHL_API_KEY=pit-fdf8bee7-9c21-4748-b265-e732781c8b3f
GHL_LOCATION_ID=PMgbQ375TEGOyGXsKz7e
```

## Deployment Instructions

1. Create the application locally first
2. Test with ngrok to ensure WebSocket works
3. Deploy to Railway using their CLI
4. Update Twilio webhook to point to Railway URL
5. Test with actual phone calls

## Success Criteria

The voice agent is complete when:
- It answers incoming calls in real-time
- It responds conversationally with low latency
- Full transcripts appear in GHL after calls
- The system handles multiple concurrent calls
- Audio quality is clear in both directions

---

## Development Log

Claude Code, log all your actions below as you build this:

### Session Started: [timestamp]

### Files Created:
- [ ] File: 
  - Purpose: 
  - Status: 

### API Integrations Tested:
- [ ] Cloudflare Whisper STT: 
- [ ] Cloudflare LLM: 
- [ ] ElevenLabs TTS: 
- [ ] GHL Webhook: 

### Deployment Steps:
- [ ] Local testing with ngrok: 
- [ ] Railway deployment: 
- [ ] Twilio webhook configuration: 

### Issues Encountered:
- Issue: 
  - Resolution: 

### Final Deployment URL:
- Railway URL: 
- Webhook endpoint: 
- WebSocket endpoint: 

### Testing Results:
- Test call #1: 
- Audio quality: 
- Response latency: 
- GHL integration: 

### Additional Notes:

---

END OF INSTRUCTIONS
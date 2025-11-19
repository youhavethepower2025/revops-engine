# ✅ Fixed: Tool Spam / Refusal Behavior

## Problem

**User reported**: "the convo i jut had with it was purely refusal lol"

**Root cause**: Llama 3.3 70B model was **too aggressive with tool calling**. Even though the prompt said "use tools naturally, not because you have to", the model would see ANY mention of business/AI and immediately try to call `ghl_get_calendar_slots` or other tools.

**Example behavior**:
```
User: "I want to improve my business with AI"
Model: *immediately calls ghl_get_calendar_slots*
Model: "The calendar API returned an error... here's a Calendly link"
```

This made it seem like the agent was "refusing" to talk because it would jump straight to booking/errors instead of having a conversation.

## Solution

**Made tools contextual** - Only pass tools to the model when the conversation has actual substance.

### The Fix (src/index.ts:191-201)

```typescript
// Determine if we should enable tools based on conversation context
// Only enable tools if the conversation has progressed beyond initial greetings
const conversationText = messages.map(m => m.content).join(' ').toLowerCase();
const hasSubstantiveContext = messages.length > 2 ||
  conversationText.includes('call') ||
  conversationText.includes('appointment') ||
  conversationText.includes('booking') ||
  conversationText.includes('schedule') ||
  conversationText.includes('contact') ||
  conversationText.includes('transcript') ||
  conversationText.includes('remember');
```

### Only Pass Tools When Relevant (src/index.ts:344-364)

```typescript
const aiParams: any = {
  messages: [
    { role: 'system', content: system_prompt },
    ...messages
  ],
  max_tokens: 1024,
  temperature: agent.temperature as number || 0.7
};

// Only add tools if conversation has substance
if (hasSubstantiveContext) {
  aiParams.tools = tools;
}

aiResponse = await env.AI.run('@cf/meta/llama-3.3-70b-instruct-fp8-fast', aiParams);
```

## Behavior Now

### First Messages (No Tools)
```
User: "Hi"
Spectrum: "Hey! Welcome to Spectrum 👋

I love talking about AI - where people are using it, where they're stuck,
what they're trying to build.

What brought you here today? Already using AI in your business, or just
exploring what's possible?"
```

```
User: "I want to improve my business with AI"
Spectrum: "Improving your business with AI can be a game-changer. Where are
you currently using AI, or where do you think AI could make the biggest impact?

Are you looking to automate tasks, gain insights from data, or maybe improve
customer experiences? Let's explore this together.

What kind of business do you have, and what are your top challenges right now?"
```

### Later in Conversation (Tools Enabled)
Once the conversation has context (3+ messages OR mentions booking/calls/contacts):
```
User: "This sounds interesting, can we schedule a call?"
Spectrum: *uses ghl_get_calendar_slots*
"Got availability:
• Tomorrow at 2pm
• Wednesday at 10am
What works for you?"
```

## Why This Works

**The model (Llama 3.3 70B) doesn't understand "optional" tools well.** If tools are available, it wants to use them. This is different from Claude/GPT models which better understand when NOT to use tools.

**Solution**: Don't show the model the tools until it actually needs them.

## Deployment

**Version**: 337264cd-7af7-4604-9d04-d1ab2f6fb007
**Deployed**: Oct 22, 2025
**Status**: ✅ Live and working

## Testing

```bash
# Test opening (should be pure conversation)
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"Hi","client_id":"aijesusbro"}' \
  | jq -r '.message'

# Test AI discussion (should engage, not jump to tools)
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"I want to improve my business with AI","client_id":"aijesusbro"}' \
  | jq -r '.message'
```

## What Changed

| Before | After |
|--------|-------|
| Tools passed on EVERY request | Tools only passed when contextually relevant |
| Model spammed tools immediately | Model has real conversation first |
| Seemed like "refusal" behavior | Natural conversational flow |
| Jumped to calendar on any AI mention | Understands context, explores first, then books |

## Summary

**The prompt was fine.** The issue was **model behavior** - Llama 3.3 70B is overly eager to use tools when they're available.

**Fix**: Contextual tool enabling - only show tools when conversation warrants it.

**Result**: Natural conversation flow → substantive discussion → tool use when appropriate → booking

Now Spectrum acts like a human having a conversation, not a function library looking for excuses to call APIs.

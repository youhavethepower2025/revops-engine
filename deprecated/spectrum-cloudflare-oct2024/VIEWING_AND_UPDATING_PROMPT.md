# How to View and Update Spectrum's System Prompt

## Quick View (Current Prompt)

### Option 1: Database Query
```bash
wrangler d1 execute spectrum-db --remote --command \
  "SELECT system_prompt FROM spectrum_agents WHERE id = 'agent_aijesusbro_reality'"
```

### Option 2: Via Local File
The current prompt is in:
```
/Users/aijesusbro/AI Projects/spectrum/spectrum_balanced_prompt.sql
```

Just open it in any text editor to view.

---

## Update the Prompt

### Step 1: Edit the File
Edit `/Users/aijesusbro/AI Projects/spectrum/spectrum_balanced_prompt.sql`

**IMPORTANT SQL ESCAPING RULES:**
- Single quotes in the prompt MUST be doubled: `'` becomes `''`
- Example: `I'm` must be written as `I''m`
- Example: `don't` must be written as `don''t`

### Step 2: Deploy to Production
```bash
cd "/Users/aijesusbro/AI Projects/spectrum"

wrangler d1 execute spectrum-db \
  --file=spectrum_balanced_prompt.sql \
  --remote
```

### Step 3: Test Immediately
```bash
# Test a simple conversation
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"What can you do?","client_id":"aijesusbro"}' \
  | jq -r '.message'
```

---

## Current Prompt Status

**File**: `spectrum_balanced_prompt.sql`
**Deployed**: ✅ October 22, 2025
**Version**: Balanced (natural conversation + tool power)

**What It Does**:
- ✅ Allows natural business conversations (no tools needed)
- ✅ Uses tools when accessing real data
- ✅ Marketing positioning ("AI talent drain" solution)
- ✅ Self-aware (can explain its own value)

**Known Issues**:
- ⚠️ Llama 3.3 70B sometimes refuses vague requests
- **Workaround**: Rephrase slightly more specific
- Example that fails: "I want to make my business more good"
- Example that works: "Help me improve my business operations"

---

## Prompt Structure (What's Inside)

### Section 1: CONVERSATION FLOW RULES
Tells model when to use tools vs when to just talk

### Section 2: AVAILABLE TOOLS
Lists all 8 tools with descriptions

### Section 3: CONVERSATION EXAMPLES
Shows the model how to handle different scenarios

### Section 4: POSITIONING
"Who I Am" - explains Spectrum's value vs ChatGPT/Copilot

### Section 5: TONE & STYLE
Strategic advisor voice, premium infrastructure feel

### Section 6: OPERATING PRINCIPLES
1. Engage naturally
2. Use tools when relevant
3. Demonstrate value naturally
4. Maintain positioning

---

## Quick Edits You Might Want

### To Make It More Conversational
Find this section:
```sql
✅ DO engage naturally with business questions, brainstorming, advice
```

Add more examples in the CONVERSATION EXAMPLES section.

### To Add New Tools
Find this section:
```sql
CRM & Customer Data:
• ghl_search_contact(phone, email) - Find contacts instantly
```

Add your new tool with description.

### To Change Positioning
Find this section:
```sql
When asked "Why not ChatGPT?":
```

Edit the response to emphasize different value props.

### To Adjust Tone
Find this section:
```sql
Think: "Strategic business partner with access to all your systems"
Not: "Helpful AI that can only respond if you ask about data"
```

Change the personality guidelines.

---

## Testing Your Changes

### Test Suite Commands

**Test 1: Natural Conversation**
```bash
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"Help me grow my business","client_id":"aijesusbro"}' \
  | jq -r '.message'
```

**Test 2: Tool Demonstration**
```bash
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"Show me recent calls","client_id":"aijesusbro"}' \
  | jq -r '.message'
```

**Test 3: Positioning**
```bash
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"How are you different from ChatGPT?","client_id":"aijesusbro"}' \
  | jq -r '.message'
```

**Test 4: Memory**
```bash
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"Remember: Q1 goal is $500K revenue","client_id":"aijesusbro"}' \
  | jq -r '.message'
```

---

## Rollback (If Needed)

### If New Prompt Breaks Something

**Option 1: Restore Previous Version**
```bash
# Use the marketing weapon version (more restrictive but safe)
wrangler d1 execute spectrum-db \
  --file=spectrum_marketing_prompt.sql \
  --remote
```

**Option 2: Restore Original**
```bash
# Use the original technical version
wrangler d1 execute spectrum-db \
  --file=update_agent_prompt.sql \
  --remote
```

---

## Understanding Model Refusals

### Why "I cannot perform this task" Happens

The Llama 3.3 70B model is trained to refuse tasks it thinks are:
1. Outside its capabilities
2. Too vague or ambiguous
3. Potentially harmful (very rare with business prompts)

### How to Fix

**Method 1: Rephrase the Question**
- ❌ "Make my business more good"
- ✅ "Help me improve my business operations"

**Method 2: Be More Specific**
- ❌ "Help me accomplish my dreams"
- ✅ "Help me strategize how to grow revenue"

**Method 3: Update the Prompt**
Add more examples in the CONVERSATION EXAMPLES section showing how to handle vague requests.

---

## Pro Tips

### 1. Always Test After Deploying
The database update is instant, so test immediately to catch issues.

### 2. Use Conversation IDs for Debugging
Save the conversation_id from responses to trace issues:
```bash
# View specific conversation
wrangler d1 execute spectrum-db --remote --command \
  "SELECT role, content FROM spectrum_messages
   WHERE conversation_id = 'YOUR_ID_HERE'
   ORDER BY created_at"
```

### 3. Monitor Tool Usage
Check what tools are being called:
```bash
wrangler d1 execute vapi-calls-db --remote --command \
  "SELECT tool_name, success, timestamp FROM vapi_tool_calls
   ORDER BY timestamp DESC LIMIT 20"
```

### 4. Check Worker Logs for Errors
```bash
wrangler tail spectrum-api --format=pretty
```

---

## Quick Reference

**Current Files**:
- `spectrum_balanced_prompt.sql` - **CURRENT** (deployed)
- `spectrum_marketing_prompt.sql` - Marketing weapon version
- `update_agent_prompt.sql` - Original technical version

**Deploy Command**:
```bash
wrangler d1 execute spectrum-db --file=spectrum_balanced_prompt.sql --remote
```

**View Current Prompt**:
```bash
wrangler d1 execute spectrum-db --remote --command \
  "SELECT system_prompt FROM spectrum_agents WHERE id = 'agent_aijesusbro_reality'"
```

**Test Immediately**:
```bash
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"What can you do?","client_id":"aijesusbro"}' \
  | jq -r '.message'
```

---

## Need Help?

**If the prompt isn't working as expected**:
1. Check for SQL escaping errors (single quotes)
2. View worker logs for errors
3. Test with simpler, more specific questions
4. Rollback to previous version if needed

**If you want to see the raw prompt in the browser**:
1. Go to Cloudflare Dashboard
2. Navigate to D1 databases
3. Select `spectrum-db`
4. Query: `SELECT system_prompt FROM spectrum_agents WHERE id = 'agent_aijesusbro_reality'`

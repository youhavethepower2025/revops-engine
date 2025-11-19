# 🔧 MANUAL SETUP GUIDE - AI JESUS BRO

Since Twilio auth is being tricky, here's the manual setup path:

## 1️⃣ RETELL DASHBOARD SETUP

### Add Twilio to Retell:
1. Go to [dashboard.retellai.com](https://dashboard.retellai.com)
2. Navigate to Phone Numbers → Add Provider
3. Select Twilio
4. Enter:
   - Account SID: `ACd7564cf277675642888a72f63d1655a3`
   - Auth Token: (get fresh one from Twilio console)
5. Save

### Import Phone Numbers:
1. Click "Import from Twilio"
2. Select all these numbers:
   - ✅ +13239685736 (primary - free from Vapi!)
   - +17027109167
   - +17027186386
   - +17027104257
   - +17027124212
   - +17027104174
   - +18669658975

### Create AI Agent:
1. Go to Agents → Create New
2. Name: "AI Jesus Bro Assistant"
3. Add the prompt from `configure_retell.py`
4. Set webhook URL:
   - Local testing: `http://[YOUR_IP]:8081/webhooks/retell`
   - Production: `http://[DO_DROPLET_IP]:8080/webhooks/retell`

## 2️⃣ TWILIO CONSOLE SETUP

For each phone number:
1. Go to Phone Numbers → Manage → Active Numbers
2. Click on each number
3. In Voice Configuration:
   - Webhook: `https://api.retellai.com/twilio-voice-webhook/[AGENT_ID]`
   - Method: POST
4. Save

## 3️⃣ DEPLOY TO DIGITAL OCEAN

```bash
# From your local machine
cd /Users/aijesusbro/AI\ Projects
python3 do_brain_deploy.py aijesusbro
```

This will:
- Create a droplet with your brain
- Set up PostgreSQL
- Return the public IP

## 4️⃣ UPDATE WEBHOOKS TO PRODUCTION

Once deployed, update:
1. Retell agent webhook to: `http://[DROPLET_IP]:8080/webhooks/retell`
2. GHL webhooks (if needed): `http://[DROPLET_IP]:8080/webhooks/ghl`

## 5️⃣ TEST THE SYSTEM

Call any of your numbers and verify:
- Call connects
- AI agent responds
- Check brain logs: `docker logs aijesusbro-brain`
- Check GHL for contact creation

---

## 🚀 QUICK DEPLOY COMMAND

If you want to just deploy now and configure voice later:

```bash
python3 do_brain_deploy.py aijesusbro
```

Your brain is READY - it's just the Twilio←→Retell connection that needs manual config!
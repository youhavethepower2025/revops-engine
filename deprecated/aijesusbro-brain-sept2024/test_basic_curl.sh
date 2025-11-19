#!/bin/bash
# Test with basic curl to see raw response

echo "Testing Twilio API with your credentials..."
echo "Account SID: ACd7564cf277675642888a72f63d1655a3"
echo "Auth Token: e65397c32f16f83469ee9d859308eb6a"
echo ""

# Test 1: Basic account info
echo "Test 1: Account info"
curl -X GET \
  https://api.twilio.com/2010-04-01/Accounts/ACd7564cf277675642888a72f63d1655a3.json \
  -u ACd7564cf277675642888a72f63d1655a3:e65397c32f16f83469ee9d859308eb6a \
  -H "Content-Type: application/json" \
  -v 2>&1 | grep -E "HTTP/|{" | head -20

echo ""
echo "Test 2: Different endpoint (usage records)"
curl -X GET \
  https://api.twilio.com/2010-04-01/Accounts/ACd7564cf277675642888a72f63d1655a3/Usage/Records.json \
  -u ACd7564cf277675642888a72f63d1655a3:e65397c32f16f83469ee9d859308eb6a \
  2>&1 | head -20
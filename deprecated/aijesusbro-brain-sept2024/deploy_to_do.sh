#!/bin/bash
# Deploy AI Jesus Bro Brain to Digital Ocean

echo "🚀 DEPLOYING AI JESUS BRO BRAIN TO DIGITAL OCEAN"
echo "================================================="

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "📦 Installing Digital Ocean CLI..."
    brew install doctl
fi

# Authenticate
export DO_API_TOKEN="dop_v1_d6b57ed13fcf3d16324a3682ab6012cd1c9ff1281d4ba7e63ad86d3a13bf2cab"
doctl auth init -t $DO_API_TOKEN

echo "✅ Authenticated with Digital Ocean"

# Create droplet with Docker pre-installed
echo ""
echo "🖥️ Creating Droplet..."
doctl compute droplet create \
  brain-aijesusbro \
  --region sfo3 \
  --size s-2vcpu-4gb \
  --image docker-20-04 \
  --enable-monitoring \
  --tag-name brain,aijesusbro \
  --user-data-file user-data.sh \
  --wait

# Get the droplet IP
echo ""
echo "📍 Getting Droplet IP..."
DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header | grep brain-aijesusbro | awk '{print $2}')

echo "✅ Droplet created: $DROPLET_IP"

# Create managed database (optional - can use Docker postgres instead)
echo ""
echo "Create managed PostgreSQL? (y/n)"
read -r CREATE_DB

if [ "$CREATE_DB" = "y" ]; then
    echo "🗄️ Creating Managed PostgreSQL..."
    doctl databases create \
      brain-db-aijesusbro \
      --engine pg \
      --size db-s-1vcpu-1gb \
      --region sfo3 \
      --version 15
fi

echo ""
echo "================================================="
echo "✅ DEPLOYMENT INITIATED!"
echo "================================================="
echo ""
echo "Droplet IP: $DROPLET_IP"
echo ""
echo "🔗 Next Steps:"
echo "1. Wait 3-5 minutes for setup to complete"
echo "2. SSH into droplet: ssh root@$DROPLET_IP"
echo "3. Check logs: docker logs aijesusbro-brain"
echo "4. Update Retell webhook to: http://$DROPLET_IP:8080/webhooks/retell"
echo ""
echo "📊 To monitor:"
echo "doctl compute droplet list"
echo "doctl compute ssh brain-aijesusbro"
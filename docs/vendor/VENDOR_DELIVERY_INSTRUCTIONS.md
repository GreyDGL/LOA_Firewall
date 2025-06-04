# LLM Firewall - Vendor Delivery Instructions

Follow these steps to create and test a secure client delivery package on AWS.

## Prerequisites

1. **Local Environment Setup:**
   ```bash
   # Ensure you're in the project directory
   cd /path/to/LoAFirewall
   
   # Verify required files exist
   ls -la deployment/docker/Dockerfile.client deployment/scripts/build_client_image.py deployment/scripts/deploy.sh
   
   # Make scripts executable
   chmod +x deployment/scripts/deploy.sh deployment/scripts/build_client_image.py
   ```

2. **AWS Environment:**
   - AWS CLI configured with appropriate permissions
   - EC2 instance or local Docker environment
   - Optional: Private ECR registry for secure distribution

## Step 1: Generate Master Secret Key

```bash
# Generate a secure master secret (save this securely!)
MASTER_SECRET=$(openssl rand -base64 32)
echo "Master Secret: $MASTER_SECRET"

# Save to environment file (for your records only)
echo "LLM_FIREWALL_SECRET=$MASTER_SECRET" > .env.master
```

## Step 2: Build Secure Client Image

```bash
# Build client image with 6-month license
PYTHONPATH=/path/to/LoAFirewall python3 deployment/scripts/build_client_image.py \
  --customer "AWS Test Client" \
  --secret "$MASTER_SECRET" \
  --days 180 \
  --tag "llm-firewall:aws-test-v1.0" \
  --compose

# This creates:
# - Docker image: llm-firewall:aws-test-v1.0
# - client_info_AWS_Test_Client.json (license details)
# - docker-compose.AWS_Test_Client.yml (deployment config)
```

## Step 3: Verify Secure Build

```bash
# Check that source code is not in the image
docker run --rm llm-firewall:aws-test-v1.0 find /app -name "*.py" | head -10

# Should show no .py files, only .pyc files
docker run --rm llm-firewall:aws-test-v1.0 ls -la /app/

# Verify license is embedded
docker run --rm llm-firewall:aws-test-v1.0 ls -la /app/license.key
```

## Step 4: Export for Client Distribution

Choose one of these methods:

### Method A: Docker Image Export (Recommended for Testing)
```bash
# Export image to tar file
docker save llm-firewall:aws-test-v1.0 > aws-test-firewall.tar

# Create client delivery package
mkdir aws-client-delivery
cp aws-test-firewall.tar aws-client-delivery/
cp client_info_AWS_Test_Client.json aws-client-delivery/
cp docker-compose.AWS_Test_Client.yml aws-client-delivery/docker-compose.yml

# Create deployment script for client
cat > aws-client-delivery/deploy.sh << 'EOF'
#!/bin/bash
echo "Loading LLM Firewall image..."
docker load < aws-test-firewall.tar

echo "Creating logs directory..."
mkdir -p logs

echo "Starting LLM Firewall..."
docker-compose up -d

echo "Waiting for service to start..."
sleep 30

echo "Testing health endpoint..."
curl -f http://localhost:5001/health

echo "Deployment complete!"
echo "Access the firewall at: http://localhost:5001"
EOF

chmod +x aws-client-delivery/deploy.sh
```

### Method B: Private ECR Registry (Production Method)
```bash
# Create ECR repository
aws ecr create-repository --repository-name llm-firewall-clients

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag and push image
docker tag llm-firewall:aws-test-v1.0 \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-firewall-clients:aws-test-v1.0

docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-firewall-clients:aws-test-v1.0
```

## Step 5: Test Client Deployment on AWS

### Launch EC2 Instance for Testing:
```bash
# Launch EC2 instance (adjust as needed)
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-your-security-group \
  --subnet-id subnet-your-subnet \
  --user-data file://user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=LLM-Firewall-Test}]'
```

### User Data Script (user-data.sh):
```bash
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install docker-compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create deployment directory
mkdir -p /home/ec2-user/firewall-deployment
chown ec2-user:ec2-user /home/ec2-user/firewall-deployment
```

### Copy Client Package to EC2:
```bash
# Get instance IP
INSTANCE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=LLM-Firewall-Test" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)

# Copy client package
scp -r aws-client-delivery/* ec2-user@$INSTANCE_IP:~/firewall-deployment/
```

### Deploy on EC2:
```bash
# SSH to instance
ssh ec2-user@$INSTANCE_IP

# Navigate to deployment directory
cd ~/firewall-deployment

# Run deployment
./deploy.sh

# Test the deployment
curl http://localhost:5001/health

# Test content checking
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello world, this is a test message"}'
```

## Step 6: Validate Security

### Check Source Code Protection:
```bash
# SSH to EC2 instance
ssh ec2-user@$INSTANCE_IP

# Try to find source code in container
docker exec llm-firewall find /app -name "*.py" | wc -l  # Should be 0

# Check what files are actually present
docker exec llm-firewall ls -la /app/

# Verify license is working
docker logs llm-firewall | grep -i license
```

### Verify License Enforcement:
```bash
# Check license validation in logs
docker logs llm-firewall | grep -E "(license|expir)" | tail -10

# Test API access
curl http://localhost:5001/health | jq
```

## Step 7: Create Client Documentation

Create a README for your client:

```bash
cat > aws-client-delivery/CLIENT_README.md << 'EOF'
# LLM Firewall Deployment

## Quick Start

1. Load the Docker image:
   ```bash
   docker load < aws-test-firewall.tar
   ```

2. Start the firewall:
   ```bash
   docker-compose up -d
   ```

3. Test deployment:
   ```bash
   curl http://localhost:5001/health
   ```

## Usage

Check content safety:
```bash
curl -X POST http://localhost:5001/check \
  -H "Content-Type: application/json" \
  -d '{"content": "Your content here"}'
```

## Support

Contact your vendor for license renewal and support.
EOF
```

## Step 8: Test License Expiration (Optional)

To test license expiration behavior:

```bash
# Create a short-term license for testing (1 day)
PYTHONPATH=/path/to/LoAFirewall python3 deployment/scripts/build_client_image.py \
  --customer "Expiration Test" \
  --secret "$MASTER_SECRET" \
  --days 1 \
  --tag "llm-firewall:expiration-test" \
  --compose

# Deploy and wait 24+ hours to see expiration behavior
```

## Step 9: Clean Up Test Resources

```bash
# Stop and remove containers
docker-compose down
docker rmi llm-firewall:aws-test-v1.0

# Terminate EC2 instance
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0

# Delete ECR repository (if created)
aws ecr delete-repository --repository-name llm-firewall-clients --force
```

## Delivery Package Checklist

When delivering to actual clients, ensure the package contains:

- [ ] Docker image file (.tar) or registry access instructions
- [ ] docker-compose.yml configured for their environment (generated from docker-compose.Customer_Name.yml)
- [ ] CLIENT_DEPLOYMENT.md (comprehensive guide)
- [ ] CLIENT_README.md (quick start guide)
- [ ] deploy.sh script for easy setup
- [ ] client_info_Customer_Name.json with license details
- [ ] Support contact information

## Security Validation Checklist

Before delivery, verify:

- [ ] No .py source files in Docker image
- [ ] License properly embedded and functioning
- [ ] Build scripts and development tools excluded
- [ ] Health checks working correctly
- [ ] API endpoints responding properly
- [ ] License expiration enforcement working
- [ ] No sensitive information in logs
- [ ] Image size reasonable (no unnecessary files)

## Production Recommendations

For actual client deliveries:

1. **Use Private Registry**: Deploy to ECR or private Docker registry
2. **Secure Communications**: Use HTTPS and VPN for image distribution
3. **License Tracking**: Maintain database of issued licenses
4. **Support Process**: Establish clear support and renewal procedures
5. **Legal Protection**: Include appropriate licensing agreements
6. **Monitoring**: Consider telemetry for license compliance

## Expected Results

After following these steps, you should have:

1. ✅ Secure Docker image with no source code exposure
2. ✅ Working firewall with embedded license
3. ✅ Complete client deployment package
4. ✅ Verified deployment on AWS infrastructure
5. ✅ Documentation for client delivery
6. ✅ Tested license enforcement mechanism

## Troubleshooting

**Image won't start:**
- Check Docker logs: `docker logs llm-firewall`
- Verify license validation in logs
- Ensure sufficient resources (2GB+ RAM)

**Health check fails:**
- Wait 60 seconds for full startup
- Check port 5001 accessibility
- Verify license hasn't expired

**License errors:**
- Verify master secret matches generation secret
- Check license file exists in container
- Validate license expiration date

Contact development team if issues persist with deployment process.
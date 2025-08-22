# Google Ads Management Tool (code generated with Claude Code)

A Streamlit-based web application for managing Google Ads campaigns with comprehensive audit logging and tracking capabilities.

## Features

- Campaign, Ad Group, and Keyword Management
- Bidding Strategy Configuration
- Ad Extensions Management
- Conversion Tracking Setup
- Comprehensive Audit Logging with User Tracking
- Real-time Performance Monitoring
- Export Capabilities

## Architecture

- **Frontend**: Streamlit web application
- **Backend**: Google Ads API v20
- **Database**: SQLite for audit logs
- **Authentication**: OAuth2 with Google Ads API

## Prerequisites

### Google Ads API Requirements
- Google Ads Developer Token (Basic level or higher)
- Google Cloud Project with Google Ads API enabled
- OAuth2 credentials (Client ID and Secret)
- Access to Google Ads account(s)

### System Requirements
- Python 3.8+
- Internet connectivity for Google Ads API calls
- 512MB+ RAM
- 1GB+ disk space for logs and data

## Setup Options

### Option 1: Local Development

#### 1. Clone and Install Dependencies
```bash
git clone <repository-url>
cd project-2
pip install -r requirements.txt
```

#### 2. Environment Configuration
Create a `.env` file in the root directory:

```env
# Required: Google Ads API Credentials
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=your_oauth_client_id
GOOGLE_ADS_CLIENT_SECRET=your_oauth_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_CUSTOMER_ID=1234567890

# Optional: For Manager Accounts only
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_manager_account_id

# Optional: Application Configuration
PORT=8501
HOST=0.0.0.0
```

#### 3. OAuth2 Setup
Run the OAuth setup script to generate refresh token:
```bash
python setup_oauth.py
```

#### 4. Start the Application
```bash
streamlit run main.py --server.port 8501 --server.address 0.0.0.0
```

### Option 2: Google Cloud Platform Deployment

#### 2.1: Cloud Run Deployment (Recommended)

##### Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

##### Deploy to Cloud Run
```bash
# Build and deploy
gcloud run deploy google-ads-tool \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8501 \
    --memory 1Gi \
    --cpu 1 \
    --set-env-vars="GOOGLE_ADS_DEVELOPER_TOKEN=${GOOGLE_ADS_DEVELOPER_TOKEN}" \
    --set-env-vars="GOOGLE_ADS_CLIENT_ID=${GOOGLE_ADS_CLIENT_ID}" \
    --set-env-vars="GOOGLE_ADS_CLIENT_SECRET=${GOOGLE_ADS_CLIENT_SECRET}" \
    --set-env-vars="GOOGLE_ADS_REFRESH_TOKEN=${GOOGLE_ADS_REFRESH_TOKEN}" \
    --set-env-vars="GOOGLE_ADS_CUSTOMER_ID=${GOOGLE_ADS_CUSTOMER_ID}"
```

##### Using Secret Manager (Recommended for Production)
```bash
# Store sensitive credentials in Secret Manager
gcloud secrets create google-ads-developer-token --data-file=token.txt
gcloud secrets create google-ads-client-secret --data-file=secret.txt
gcloud secrets create google-ads-refresh-token --data-file=refresh.txt

# Deploy with secret references
gcloud run deploy google-ads-tool \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets="GOOGLE_ADS_DEVELOPER_TOKEN=google-ads-developer-token:latest" \
    --set-secrets="GOOGLE_ADS_CLIENT_SECRET=google-ads-client-secret:latest" \
    --set-secrets="GOOGLE_ADS_REFRESH_TOKEN=google-ads-refresh-token:latest" \
    --set-env-vars="GOOGLE_ADS_CLIENT_ID=${GOOGLE_ADS_CLIENT_ID}" \
    --set-env-vars="GOOGLE_ADS_CUSTOMER_ID=${GOOGLE_ADS_CUSTOMER_ID}"
```

#### 2.2: App Engine Deployment

##### Create app.yaml
```yaml
runtime: python39

env_variables:
  GOOGLE_ADS_CLIENT_ID: your_client_id
  GOOGLE_ADS_CUSTOMER_ID: your_customer_id

automatic_scaling:
  min_instances: 0
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 1
  disk_size_gb: 10
```

##### Deploy
```bash
gcloud app deploy
```

#### 2.3: Compute Engine Deployment

##### Bootstrap Script (bootstrap.sh)
```bash
#!/bin/bash

# Update system
sudo apt-get update
sudo apt-get install -y python3 python3-pip git

# Clone repository
git clone <repository-url> /opt/google-ads-tool
cd /opt/google-ads-tool

# Install dependencies
pip3 install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/google-ads-tool.service > /dev/null <<EOF
[Unit]
Description=Google Ads Management Tool
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/google-ads-tool
Environment=PATH=/usr/bin:/usr/local/bin
EnvironmentFile=/opt/google-ads-tool/.env
ExecStart=/usr/local/bin/streamlit run main.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl enable google-ads-tool
sudo systemctl start google-ads-tool
```

##### Create VM Instance
```bash
gcloud compute instances create google-ads-tool \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --metadata-from-file startup-script=bootstrap.sh \
    --tags=http-server,https-server \
    --service-account=your-service-account@project.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/cloud-platform
```

## Security Considerations

### API Token Protection
1. **Never commit tokens to version control**
2. **Use environment variables or Secret Manager**
3. **Implement proper IAM roles and permissions**
4. **Regular token rotation**

### Rate Limiting and Throttling Prevention
1. **API quotas are per developer token**
2. **Implement request queuing and retry logic**
3. **Monitor API usage in Google Cloud Console**
4. **Use separate tokens for different environments**

### Access Control
```bash
# Create IAM roles for different access levels
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:analyst@company.com" \
    --role="roles/viewer"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:manager@company.com" \
    --role="roles/editor"
```

## Production Deployment Checklist

### Before Deployment
- [ ] Environment variables configured
- [ ] OAuth2 credentials obtained
- [ ] API quotas sufficient for expected usage
- [ ] Backup strategy for audit logs
- [ ] Monitoring and alerting configured

### GCP Resource Requirements
```yaml
# Minimum Resources
CPU: 1 vCPU
Memory: 1GB RAM
Storage: 10GB (for logs and temporary data)
Network: Standard internet egress

# Estimated Costs (us-central1)
Cloud Run: ~$15-30/month (depending on usage)
App Engine: ~$25-50/month
Compute Engine: ~$25-40/month (e2-medium)
```

### Monitoring Setup
```bash
# Enable monitoring APIs
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

# Create alerting policies for high API usage
gcloud alpha monitoring policies create --policy-from-file=alert-policy.yaml
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Yes | Your Google Ads API developer token |
| `GOOGLE_ADS_CLIENT_ID` | Yes | OAuth2 client ID |
| `GOOGLE_ADS_CLIENT_SECRET` | Yes | OAuth2 client secret |
| `GOOGLE_ADS_REFRESH_TOKEN` | Yes | OAuth2 refresh token |
| `GOOGLE_ADS_CUSTOMER_ID` | Yes | Target Google Ads account ID |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | No | Manager account ID (if applicable) |
| `PORT` | No | Application port (default: 8501) |
| `HOST` | No | Host address (default: 0.0.0.0) |

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Verify OAuth2 setup and token validity
2. **API Quota Exceeded**: Check usage in Google Cloud Console
3. **Permission Denied**: Verify account access and API permissions
4. **Rate Limiting**: Implement exponential backoff in API calls

### Logs and Debugging
- Application logs: Available in Streamlit console
- Audit logs: Stored in SQLite database (`audit_logs.db`)
- GCP logs: Available in Cloud Logging

### Health Checks
```bash
# Local health check
curl http://localhost:8501/_stcore/health

# Cloud Run health check
curl https://your-service-url.run.app/_stcore/health
```

## Support and Maintenance

### Regular Maintenance Tasks
1. **Token Rotation**: Update refresh tokens as needed
2. **Log Cleanup**: Archive old audit logs
3. **Dependency Updates**: Keep packages up to date
4. **Backup Management**: Regular backup of audit data

### Monitoring Metrics
- API request volume and latency
- Error rates and types
- User activity and audit trail
- Resource utilization

For technical support or questions, please contact the development team.

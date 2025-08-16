#!/bin/bash

# Google Ads Tool Bootstrap Script for GCP Compute Engine
# This script sets up the Google Ads management tool on a fresh Ubuntu instance

set -e

# Configuration
APP_DIR="/opt/google-ads-tool"
SERVICE_USER="google-ads"
SERVICE_NAME="google-ads-tool"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Update system packages
log_info "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
log_info "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    nginx \
    supervisor \
    sqlite3

# Create service user
log_info "Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd --system --shell /bin/bash --home-dir "$APP_DIR" --create-home "$SERVICE_USER"
fi

# Clone or update repository
log_info "Setting up application directory..."
if [ -d "$APP_DIR/.git" ]; then
    log_info "Updating existing repository..."
    cd "$APP_DIR"
    sudo -u "$SERVICE_USER" git pull
else
    log_info "Cloning repository..."
    sudo rm -rf "$APP_DIR"
    sudo -u "$SERVICE_USER" git clone https://github.com/your-org/google-ads-tool.git "$APP_DIR"
fi

cd "$APP_DIR"

# Create Python virtual environment
log_info "Creating Python virtual environment..."
sudo -u "$SERVICE_USER" python3 -m venv venv
sudo -u "$SERVICE_USER" ./venv/bin/pip install --upgrade pip

# Install Python dependencies
log_info "Installing Python dependencies..."
sudo -u "$SERVICE_USER" ./venv/bin/pip install -r requirements.txt

# Create environment file template
log_info "Creating environment configuration..."
if [ ! -f "$APP_DIR/.env" ]; then
    sudo -u "$SERVICE_USER" tee "$APP_DIR/.env" > /dev/null <<EOF
# Google Ads API Configuration
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CLIENT_ID=
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=
GOOGLE_ADS_LOGIN_CUSTOMER_ID=

# Application Configuration
PORT=8501
HOST=127.0.0.1
EOF
    log_warn "Please configure the .env file with your Google Ads API credentials"
fi

# Create data directory for SQLite database
log_info "Creating data directory..."
sudo -u "$SERVICE_USER" mkdir -p "$APP_DIR/data"

# Create systemd service file
log_info "Creating systemd service..."
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null <<EOF
[Unit]
Description=Google Ads Management Tool
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/streamlit run main.py --server.port=8501 --server.address=127.0.0.1
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx reverse proxy
log_info "Configuring Nginx reverse proxy..."
sudo tee "/etc/nginx/sites-available/${SERVICE_NAME}" > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location /_stcore/health {
        proxy_pass http://127.0.0.1:8501/_stcore/health;
    }
}
EOF

# Enable Nginx site
sudo ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/"
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Create log rotation configuration
log_info "Setting up log rotation..."
sudo tee "/etc/logrotate.d/${SERVICE_NAME}" > /dev/null <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    su $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

# Create logs directory
sudo -u "$SERVICE_USER" mkdir -p "$APP_DIR/logs"

# Set up firewall rules
log_info "Configuring firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Reload systemd and enable services
log_info "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl enable nginx

# Start services
log_info "Starting services..."
sudo systemctl restart nginx
sudo systemctl start "$SERVICE_NAME"

# Wait for service to start
sleep 5

# Check service status
log_info "Checking service status..."
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    log_info "✓ Google Ads Tool service is running"
else
    log_error "✗ Google Ads Tool service failed to start"
    sudo systemctl status "$SERVICE_NAME"
fi

if sudo systemctl is-active --quiet nginx; then
    log_info "✓ Nginx is running"
else
    log_error "✗ Nginx failed to start"
    sudo systemctl status nginx
fi

# Display final information
log_info "Bootstrap completed!"
echo
echo "Next steps:"
echo "1. Configure your Google Ads API credentials in: $APP_DIR/.env"
echo "2. Restart the service: sudo systemctl restart $SERVICE_NAME"
echo "3. Access the application at: http://$(curl -s ipinfo.io/ip)"
echo
echo "Useful commands:"
echo "  Check service status: sudo systemctl status $SERVICE_NAME"
echo "  View service logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart service: sudo systemctl restart $SERVICE_NAME"
echo "  Edit configuration: sudo -u $SERVICE_USER nano $APP_DIR/.env"
echo
log_warn "Remember to configure your .env file with the actual Google Ads API credentials!"
#!/bin/bash
set -e

# Run this script from INSIDE the cloned project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/email-agent"

echo "Starting Email Agent Setup..."
echo "Source directory: $SCRIPT_DIR"
echo "Install directory: $INSTALL_DIR"

# Install Python if needed
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y python3-venv python3-pip rsync
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3 pip rsync
else
    echo "Could not detect apt or dnf. Please install python3, pip, and rsync manually."
fi

# Create install directory and copy ALL files (including hidden dot files)
sudo mkdir -p "$INSTALL_DIR"
sudo chown -R "$USER:$USER" "$INSTALL_DIR"
rsync -av --exclude='venv/' --exclude='.git/' --exclude='__pycache__/' "$SCRIPT_DIR/" "$INSTALL_DIR/"

cd "$INSTALL_DIR"

# Setup virtual environment
echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Handle .env file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo ""
        echo "Created .env from template."
        echo "PLEASE EDIT: nano $INSTALL_DIR/.env"
    else
        echo "No .env.example found. Create $INSTALL_DIR/.env manually."
    fi
else
    echo ".env file already exists, keeping it."
fi

# Setup systemd service
if [ -f email-agent.service ]; then
    echo "Setting up systemd service..."
    # Dynamically set the correct user/group for this machine
    sed -i "s/User=.*/User=$USER/" email-agent.service
    sed -i "s/Group=.*/Group=$USER/" email-agent.service
    sudo cp email-agent.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable email-agent.service
    echo "Systemd service registered for user: $USER"
else
    echo "email-agent.service not found. Skipping systemd setup."
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo "Next steps:"
echo "1. Edit your credentials:  nano $INSTALL_DIR/.env"
echo "2. Start the bot:          sudo systemctl start email-agent.service"
echo "3. Check status:           sudo systemctl status email-agent.service"
echo "4. View logs:              sudo journalctl -u email-agent.service -f"

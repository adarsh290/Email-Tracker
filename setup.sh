#!/bin/bash
set -e

echo "Starting Email Agent Setup..."

# Ensure python3-venv is installed
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y python3-venv python3-pip
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3 pip
else
    echo "Could not detect apt or dnf. Please install python3-venv and pip manually."
fi

# Create project directory
sudo mkdir -p /opt/email-agent
sudo chown -R $USER:$USER /opt/email-agent

# Copy files (assuming run from project root)
cp -r ./* /opt/email-agent/

cd /opt/email-agent

# Setup virtual environment
echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Handle .env file
if [ ! -f .env ]; then
    echo "Creating .env from template. PLEASE EDIT /opt/email-agent/.env with your credentials."
    cp .env.example .env
else
    echo ".env file already exists."
fi

# Setup systemd service
echo "Setting up systemd service..."
sudo cp email-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable email-agent.service

echo "Setup complete!"
echo "Next steps:"
echo "1. Edit your credentials: nano /opt/email-agent/.env"
echo "2. Start the bot: sudo systemctl start email-agent.service"
echo "3. Check status: sudo systemctl status email-agent.service"
echo "4. View logs: sudo journalctl -u email-agent.service -f"

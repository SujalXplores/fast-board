#!/bin/bash

# FastBoard Deployment Script for Ubuntu/Debian
# Run this script on your VPS or cloud server

set -e

echo "🚀 FastBoard Deployment Script"
echo "==============================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed successfully!"
else
    echo "Docker already installed."
fi

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt install -y docker-compose
    echo "Docker Compose installed successfully!"
else
    echo "Docker Compose already installed."
fi

# Install Git if not present
echo "📋 Installing Git..."
sudo apt install -y git curl

# Clone or update repository
if [ -d "fast-board" ]; then
    echo "📥 Updating FastBoard repository..."
    cd fast-board
    git pull origin main
else
    echo "📥 Cloning FastBoard repository..."
    git clone https://github.com/SujalXplores/fast-board.git
    cd fast-board
fi

# Setup environment file
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up environment file..."
    cp .env.example .env
    echo ""
    echo "🔑 Please edit .env file with your configuration:"
    echo "   - Set your OpenAI API key"
    echo "   - Configure production settings"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Build and start services
echo "🏗️  Building and starting FastBoard..."
docker-compose down
docker-compose build
docker-compose up -d

# Setup firewall (optional)
echo "🔥 Configuring firewall..."
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw --force enable

echo ""
echo "✅ FastBoard deployment completed!"
echo ""
echo "🌐 Your application should be available at:"
echo "   http://your-server-ip"
echo ""
echo "📊 To check logs:"
echo "   docker-compose logs -f"
echo ""
echo "🔄 To restart services:"
echo "   docker-compose restart"
echo ""

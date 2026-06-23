#!/bin/bash
# Bounty Hunter Setup Script

echo "🎯 Bounty Hunter Setup"
echo "======================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python 3 found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data reports logs
echo -e "${GREEN}✓ Directories created${NC}"

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x bounty_hunter.py scheduler.py
echo -e "${GREEN}✓ Scripts made executable${NC}"

# Check for notify-send (for desktop notifications)
echo ""
echo "Checking for desktop notification support..."
if command -v notify-send &> /dev/null; then
    echo -e "${GREEN}✓ notify-send found (desktop notifications enabled)${NC}"
else
    echo -e "${YELLOW}⚠ notify-send not found. Desktop notifications will not work.${NC}"
    echo "  Install with: sudo pacman -S libnotify (Arch) or sudo apt install libnotify-bin (Ubuntu)"
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from database import BountyDatabase; db = BountyDatabase(); print('Database initialized')"
echo -e "${GREEN}✓ Database initialized${NC}"

# Test configuration
echo ""
echo "Testing configuration..."
if [ -f "config.yaml" ]; then
    echo -e "${GREEN}✓ config.yaml found${NC}"
else
    echo -e "${RED}✗ config.yaml not found${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup complete! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment (if not already):"
echo "   ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo "2. Run your first scrape:"
echo "   ${YELLOW}python bounty_hunter.py --scrape${NC}"
echo ""
echo "3. Generate a report:"
echo "   ${YELLOW}python bounty_hunter.py --report daily${NC}"
echo ""
echo "4. Check statistics:"
echo "   ${YELLOW}python bounty_hunter.py --stats${NC}"
echo ""
echo "5. Start the scheduler (optional):"
echo "   ${YELLOW}python scheduler.py${NC}"
echo ""
echo "For more information, see README.md"
echo ""





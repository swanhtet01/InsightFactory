#!/bin/bash
# This script sets up and runs the Tyre Production KPI Dashboard

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check pip installation
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Install system dependencies for OCR
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y tesseract
elif command -v brew &> /dev/null; then
    # macOS
    brew install tesseract
else
    echo "Please install Tesseract OCR manually for your system"
fi

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/images/2025/{daily,weekly,monthly}
mkdir -p logs

# Set up environment variables
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "STREAMLIT_SERVER_PORT=8501" > .env
    echo "STREAMLIT_SERVER_ADDRESS=0.0.0.0" >> .env
    echo "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false" >> .env
fi

# Run the application
echo "Starting Tyre Production KPI Dashboard..."
streamlit run app.py

#!/bin/bash

# Setup script for OpenMP Test Generator

echo "Setting up OpenMP Test Generator..."

# Check if running on supported OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux system"
    # Install dependencies for Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt update
        sudo apt install -y build-essential cmake git llvm-14-dev libclang-14-dev clang-14 libcurl4-openssl-dev libsqlite3-dev pkg-config nlohmann-json3-dev
    # Install dependencies for CentOS/RHEL
    elif command -v yum &> /dev/null; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y cmake git llvm-devel clang-devel libcurl-devel sqlite-devel pkgconfig
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS system"
    # Install dependencies via Homebrew
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install llvm cmake curl sqlite3 nlohmann-json pkg-config
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo "Dependencies installed successfully!"

# Set up environment variables
echo "Setting up environment variables..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo 'export LLVM_DIR="/usr/lib/llvm-14"' >> ~/.bashrc
    echo 'export PATH="/usr/lib/llvm-14/bin:$PATH"' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH="/usr/lib/llvm-14/lib:$LD_LIBRARY_PATH"' >> ~/.bashrc
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo 'export LLVM_DIR="/opt/homebrew/opt/llvm"' >> ~/.zshrc
    echo 'export PATH="/opt/homebrew/opt/llvm/bin:$PATH"' >> ~/.zshrc
fi

echo "Setup complete! Please restart your terminal or run 'source ~/.bashrc' (Linux) or 'source ~/.zshrc' (macOS)"

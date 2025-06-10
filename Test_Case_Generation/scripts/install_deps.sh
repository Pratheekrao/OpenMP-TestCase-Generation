#!/bin/bash

set -e  # Exit on any error

echo "=========================================="
echo "OpenMP Test Generator Dependency Installer"
echo "=========================================="

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "ubuntu"
        elif [ -f /etc/redhat-release ]; then
            echo "centos"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo "Detected OS: $OS"

# Install dependencies based on OS
install_ubuntu_deps() {
    echo "Installing dependencies for Ubuntu/Debian..."
    
    # Update package list
    sudo apt update
    
    # Core development tools
    sudo apt install -y \
        build-essential \
        cmake \
        git \
        pkg-config \
        wget \
        curl
    
    # LLVM/Clang (try multiple versions)
    echo "Installing LLVM/Clang..."
    if sudo apt install -y llvm-17-dev libclang-17-dev clang-17; then
        export LLVM_VERSION=17
        echo "Installed LLVM 17"
    elif sudo apt install -y llvm-16-dev libclang-16-dev clang-16; then
        export LLVM_VERSION=16
        echo "Installed LLVM 16"
    elif sudo apt install -y llvm-15-dev libclang-15-dev clang-15; then
        export LLVM_VERSION=15
        echo "Installed LLVM 15"
    elif sudo apt install -y llvm-14-dev libclang-14-dev clang-14; then
        export LLVM_VERSION=14
        echo "Installed LLVM 14"
    else
        echo "Failed to install LLVM/Clang"
        exit 1
    fi
    
    # Required libraries
    sudo apt install -y \
        libcurl4-openssl-dev \
        libsqlite3-dev \
        nlohmann-json3-dev
    
    echo "LLVM_VERSION=$LLVM_VERSION" > .env
}

install_centos_deps() {
    echo "Installing dependencies for CentOS/RHEL..."
    
    # Enable EPEL repository
    sudo yum install -y epel-release
    
    # Development tools
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y cmake3 git pkg-config wget curl
    
    # LLVM/Clang
    sudo yum install -y llvm-devel clang-devel
    
    # Required libraries
    sudo yum install -y libcurl-devel sqlite-devel
    
    # Install nlohmann-json manually if not available
    if ! yum list nlohmann-json3-devel &>/dev/null; then
        echo "Installing nlohmann-json manually..."
        cd /tmp
        git clone https://github.com/nlohmann/json.git
        cd json
        mkdir build && cd build
        cmake3 .. -DJSON_BuildTests=OFF
        make -j$(nproc)
        sudo make install
        cd ../../..
    else
        sudo yum install -y nlohmann-json3-devel
    fi
    
    echo "LLVM_VERSION=14" > .env
}

install_macos_deps() {
    echo "Installing dependencies for macOS..."
    
    # Install Xcode command line tools
    if ! xcode-select -p &>/dev/null; then
        echo "Installing Xcode command line tools..."
        xcode-select --install
        echo "Please complete Xcode installation and re-run this script"
        exit 1
    fi
    
    # Install Homebrew if not present
    if ! command -v brew &>/dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for current session
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
    
    # Install dependencies
    brew install llvm cmake curl sqlite3 nlohmann-json pkg-config
    
    # Determine LLVM path
    if [[ -d "/opt/homebrew/opt/llvm" ]]; then
        echo "LLVM_DIR=/opt/homebrew/opt/llvm" > .env
        echo "LLVM_VERSION=17" >> .env
    elif [[ -d "/usr/local/opt/llvm" ]]; then
        echo "LLVM_DIR=/usr/local/opt/llvm" > .env
        echo "LLVM_VERSION=17" >> .env
    fi
}

# Main installation
case $OS in
    "ubuntu")
        install_ubuntu_deps
        ;;
    "centos")
        install_centos_deps
        ;;
    "macos")
        install_macos_deps
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

echo "=========================================="
echo "Dependencies installed successfully!"
echo "=========================================="

# Create environment setup script
create_env_setup() {
    echo "Creating environment setup script..."
    
    cat > setup_env.sh << 'EOF'
#!/bin/bash

# OpenMP Test Generator Environment Setup
echo "Setting up OpenMP Test Generator environment..."

# Load .env file if it exists
if [ -f .env ]; then
    source .env
fi

# Detect OS and set paths
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    LLVM_VERSION=${LLVM_VERSION:-14}
    export LLVM_DIR="/usr/lib/llvm-${LLVM_VERSION}"
    export PATH="/usr/lib/llvm-${LLVM_VERSION}/bin:$PATH"
    export LD_LIBRARY_PATH="/usr/lib/llvm-${LLVM_VERSION}/lib:$LD_LIBRARY_PATH"
    export PKG_CONFIG_PATH="/usr/lib/llvm-${LLVM_VERSION}/lib/pkgconfig:$PKG_CONFIG_PATH"
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if [[ -d "/opt/homebrew/opt/llvm" ]]; then
        # Apple Silicon
        export LLVM_DIR="/opt/homebrew/opt/llvm"
        export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
        export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
        export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"
    elif [[ -d "/usr/local/opt/llvm" ]]; then
        # Intel Mac
        export LLVM_DIR="/usr/local/opt/llvm"
        export PATH="/usr/local/opt/llvm/bin:$PATH"
        export LDFLAGS="-L/usr/local/opt/llvm/lib"
        export CPPFLAGS="-I/usr/local/opt/llvm/include"
    fi
fi

# CMake configuration
export CMAKE_PREFIX_PATH="$LLVM_DIR:$CMAKE_PREFIX_PATH"

# API Keys (set these manually)
# export GROQ_API_KEY="your_groq_api_key_here"
# export GITHUB_TOKEN="your_github_token_here"

echo "Environment variables set:"
echo "  LLVM_DIR: $LLVM_DIR"
echo "  PATH includes LLVM: $(echo $PATH | grep -o '[^:]*llvm[^:]*' | head -1)"

# Verify installations
echo ""
echo "Verifying installations..."

if command -v clang &>/dev/null; then
    echo "✓ Clang: $(clang --version | head -1)"
else
    echo "✗ Clang not found"
fi

if command -v cmake &>/dev/null; then
    echo "✓ CMake: $(cmake --version | head -1)"
else
    echo "✗ CMake not found"
fi

if pkg-config --exists libcurl; then
    echo "✓ libcurl: $(pkg-config --modversion libcurl)"
else
    echo "✗ libcurl not found"
fi

if command -v sqlite3 &>/dev/null; then
    echo "✓ SQLite3: $(sqlite3 --version | cut -d' ' -f1)"
else
    echo "✗ SQLite3 not found"
fi

echo ""
echo "Environment setup complete!"
echo "Run 'source setup_env.sh' to load these settings in your current shell"
EOF

    chmod +x setup_env.sh
}

create_env_setup

echo ""
echo "Next steps:"
echo "1. Run: source setup_env.sh"
echo "2. Set your API keys in setup_env.sh or as environment variables"
echo "3. Build the project: mkdir build && cd build && cmake .. && make"
echo ""

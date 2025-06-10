#!/bin/bash

# OpenMP Test Generator Environment Setup
echo "Setting up OpenMP Test Generator environment..."

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    source .env
fi

# Set project root
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Project root: $PROJECT_ROOT"

# API Keys (check if already set)
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  GROQ_API_KEY not set. Please set it in .env file or export it manually."
else
    echo "✓ GROQ_API_KEY is set"
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "ℹ️  GITHUB_TOKEN not set (optional, but recommended for higher API rate limits)"
else
    echo "✓ GITHUB_TOKEN is set"
fi

# Create necessary directories
mkdir -p "$PROJECT_ROOT/outputs"
mkdir -p "$PROJECT_ROOT/build"

echo ""
echo "Environment setup complete!"
echo ""
echo "Available commands:"
echo "  Build project:     cd build && cmake .. && make"
echo "  Run tool:          ./build/openmp-test-gen --help"
echo "  Clean build:       rm -rf build/*"
echo ""
echo "Example usage:"
echo "  ./build/openmp-test-gen --pr 67890 --stage codegen --num-tests 2"
echo ""

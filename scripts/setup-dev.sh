#!/usr/bin/env bash
#
# Development Environment Setup Script
# Sets up pre-commit hooks and dev dependencies
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Print colored message
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo "======================================"
    echo "$1"
    echo "======================================"
    echo ""
}

# Change to project root
cd "$PROJECT_ROOT"

print_header "Setting Up Development Environment"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_warning "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    print_success "uv installed"
else
    print_success "uv already installed"
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    uv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment exists"
fi

# Install dev dependencies
print_info "Installing dev dependencies..."
uv pip install -e ".[dev]"
print_success "Dev dependencies installed"

# Install pre-commit hooks
print_info "Installing pre-commit hooks..."
source .venv/bin/activate
pre-commit install --hook-type commit-msg
pre-commit install
print_success "Pre-commit hooks installed"

# Run pre-commit on all files (optional)
read -p "$(echo -e "${BLUE}?${NC} Run pre-commit on all files now? (y/N): ")" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Running pre-commit on all files..."
    pre-commit run --all-files || true
    print_success "Pre-commit check complete"
fi

print_header "Setup Complete!"

echo ""
echo "Your development environment is ready! 🎉"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source .venv/bin/activate"
echo "  2. Make changes to the code"
echo "  3. Commit using: cz commit (or git commit)"
echo "  4. Pre-commit hooks will run automatically"
echo ""
echo "Useful commands:"
echo "  • cz commit          - Interactive commit with commitizen"
echo "  • cz bump            - Bump version automatically"
echo "  • pre-commit run     - Run hooks manually"
echo "  • pytest             - Run tests"
echo "  • ruff format .      - Format code"
echo "  • ruff check .       - Lint code"
echo ""

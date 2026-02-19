#!/usr/bin/env bash
#
# PySetItUp Entry Point Script
# Checks for Homebrew and Python environment before launching
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
VENV_DIR="$SCRIPT_DIR/.venv"

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

# Check if Homebrew is installed
check_homebrew() {
    print_info "Checking for Homebrew..."

    if command -v brew &> /dev/null; then
        BREW_VERSION=$(brew --version | head -n 1)
        print_success "Homebrew installed: $BREW_VERSION"
        return 0
    else
        print_warning "Homebrew not found"
        return 1
    fi
}

# Install Homebrew
install_homebrew() {
    print_header "Installing Homebrew"

    print_info "Homebrew is required to run PySetItUp"
    echo ""
    echo "This script will install Homebrew from: https://brew.sh"
    echo ""
    read -p "Continue with installation? (y/N) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Installation cancelled"
        exit 1
    fi

    print_info "Downloading and installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH for current session
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        print_success "Homebrew installed (Apple Silicon)"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
        print_success "Homebrew installed (Intel)"
    else
        print_error "Homebrew installation failed"
        exit 1
    fi
}

# Check Python version
check_python() {
    print_info "Checking for Python 3.10+..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [[ $MAJOR -ge 3 ]] && [[ $MINOR -ge 10 ]]; then
            print_success "Python $PYTHON_VERSION installed"
            return 0
        else
            print_warning "Python $PYTHON_VERSION found, but 3.10+ required"
            return 1
        fi
    else
        print_warning "Python 3 not found"
        return 1
    fi
}

# Install Python via Homebrew
install_python() {
    print_header "Installing Python"

    print_info "Installing Python 3.12 via Homebrew..."
    brew install python@3.12

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "$PYTHON_VERSION installed"
    else
        print_error "Python installation failed"
        exit 1
    fi
}

# Check if uv is installed
check_uv() {
    print_info "Checking for uv package manager..."

    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version)
        print_success "uv installed: $UV_VERSION"
        return 0
    else
        print_warning "uv not found"
        return 1
    fi
}

# Install uv
install_uv() {
    print_header "Installing uv"

    print_info "Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"

    if command -v uv &> /dev/null; then
        print_success "uv installed successfully"
    else
        print_error "uv installation failed"
        exit 1
    fi
}

# Check current shell
check_shell() {
    print_info "Checking current shell..."

    CURRENT_SHELL=$(basename "$SHELL")
    print_info "Current shell: $CURRENT_SHELL"

    if [[ "$CURRENT_SHELL" == "zsh" ]]; then
        print_success "Already using zsh"
        return 0
    else
        print_warning "Not using zsh (current: $CURRENT_SHELL)"
        return 1
    fi
}

# Check if zsh is installed
check_zsh() {
    if command -v zsh &> /dev/null; then
        ZSH_VERSION=$(zsh --version | awk '{print $2}')
        print_success "zsh installed: $ZSH_VERSION"
        return 0
    else
        print_warning "zsh not found"
        return 1
    fi
}

# Install zsh
install_zsh() {
    print_header "Installing zsh"

    print_info "Installing zsh via Homebrew..."
    brew install zsh

    if command -v zsh &> /dev/null; then
        print_success "zsh installed successfully"
    else
        print_error "zsh installation failed"
        exit 1
    fi
}

# Change default shell to zsh
setup_zsh_shell() {
    print_header "Setting up zsh as default shell"

    local ZSH_PATH=$(which zsh)
    print_info "zsh location: $ZSH_PATH"

    # Check if zsh is in /etc/shells
    if ! grep -q "$ZSH_PATH" /etc/shells 2>/dev/null; then
        print_info "Adding zsh to /etc/shells (requires sudo)..."
        echo "$ZSH_PATH" | sudo tee -a /etc/shells > /dev/null
    fi

    # Change default shell
    print_info "Changing default shell to zsh (requires sudo)..."
    if sudo chsh -s "$ZSH_PATH" "$USER"; then
        print_success "Default shell changed to zsh"
        print_warning "You'll need to restart your terminal for the change to take effect"
    else
        print_error "Failed to change default shell"
        print_warning "You can manually change it later with: chsh -s $ZSH_PATH"
        return 1
    fi
}

# Check if virtual environment exists and is valid
check_venv() {
    print_info "Checking Python virtual environment..."

    if [[ -d "$VENV_DIR" ]] && [[ -f "$VENV_DIR/bin/python" ]]; then
        print_success "Virtual environment found"
        return 0
    else
        print_warning "Virtual environment not found or invalid"
        return 1
    fi
}

# Create and setup virtual environment
setup_venv() {
    print_header "Setting up Python Environment"

    print_info "Creating virtual environment..."
    cd "$SCRIPT_DIR"

    # Remove old venv if it exists but is broken
    if [[ -d "$VENV_DIR" ]]; then
        print_info "Removing old virtual environment..."
        rm -rf "$VENV_DIR"
    fi

    # Create venv with uv (much faster than python -m venv)
    uv venv

    print_success "Virtual environment created"

    print_info "Installing dependencies..."
    uv pip install -e .

    print_success "Dependencies installed"
}

# Verify PySetItUp can be imported
verify_installation() {
    print_info "Verifying PySetItUp installation..."

    if "$VENV_DIR/bin/python" -c "from pysetitup.config.loader import load_config; from pysetitup.ui.selector import PackageSelector; print('✓ Import successful')" &> /dev/null; then
        print_success "PySetItUp is ready to run"
        return 0
    else
        print_error "PySetItUp verification failed"
        return 1
    fi
}

# Run the installer
run_installer() {
    print_header "Starting PySetItUp Installer"

    cd "$SCRIPT_DIR"

    # Check for special modes
    local preview_mode=0
    for arg in "$@"; do
        if [[ "$arg" == "--preview" ]]; then
            preview_mode=1
            break
        fi
    done

    if [[ $preview_mode -eq 1 ]]; then
        print_info "Running in preview mode (no actual installation)"
        # Pass all args except --preview to test_tui.py
        local args=()
        for arg in "$@"; do
            if [[ "$arg" != "--preview" ]]; then
                args+=("$arg")
            fi
        done
        exec "$VENV_DIR/bin/python" test_tui.py "${args[@]}"
    else
        # Run actual installer with all arguments
        exec "$VENV_DIR/bin/python" install_packages.py "$@"
    fi
}

# Main installation flow
main() {
    # Parse arguments
    PREVIEW_MODE=0
    for arg in "$@"; do
        if [[ "$arg" == "--preview" ]]; then
            PREVIEW_MODE=1
        fi
    done

    clear
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║                                        ║"
    echo "║          PySetItUp Setup               ║"
    echo "║    Mac Development Environment         ║"
    echo "║                                        ║"
    echo "╚════════════════════════════════════════╝"
    echo ""

    # Check and install Homebrew if needed
    if ! check_homebrew; then
        install_homebrew
    fi

    # Check and install Python if needed
    if ! check_python; then
        install_python
    fi

    # Check and install uv if needed
    if ! check_uv; then
        install_uv
    fi

    # Check shell and setup zsh if needed
    if ! check_shell; then
        print_info "zsh is recommended for Oh My Zsh and Powerlevel10k"
        echo ""
        read -p "Would you like to install and use zsh? (Y/n) " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            # Install zsh if not already installed
            if ! check_zsh; then
                install_zsh
            fi

            # Change default shell to zsh
            setup_zsh_shell
        else
            print_warning "Skipping zsh setup. Some features may not work optimally."
        fi
    fi

    # Check and setup venv if needed
    if ! check_venv; then
        setup_venv
    fi

    # Verify installation
    if ! verify_installation; then
        print_error "Setup failed. Please check the errors above."
        exit 1
    fi

    # Run the installer with all arguments
    run_installer "$@"
}

# Run main function with all arguments
main "$@"

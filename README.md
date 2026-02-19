# PySetItUp

**Interactive Mac development environment setup with a beautiful TUI**

Set up your Mac development environment in minutes with an interactive terminal interface. Choose packages visually, customize presets, and install everything with one command.

<p align="center">
  <a href="https://github.com/DicksonK/pysetitup/releases"><img src="https://img.shields.io/github/v/release/DicksonK/pysetitup" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/DicksonK/pysetitup" alt="License"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey" alt="macOS">
  <img src="https://img.shields.io/badge/built%20with-Python-3776AB" alt="Python">
  <img src="https://img.shields.io/badge/requires-Python%203.10+-blue" alt="Python 3.10+">
</p>

---

## Why PySetItUp?

**No more manual installation scripts.** No more copying commands from blog posts. No more forgetting what tools you need.

PySetItUp gives you:
- 🎨 **Interactive TUI** - Visual package selection with keyboard navigation
- 📦 **Curated Presets** - Start with minimal, developer, or full setups
- ⚡ **Fast & Smart** - Detects installed packages, runs checks in parallel
- 🎯 **Custom Presets** - Load your own YAML files with team configurations
- 🔍 **Preview Mode** - Test before installing anything
- ✅ **Type-Safe** - Built with Python and Pydantic for reliability

---

## Quick Start

### Option 1: Run Directly (Recommended)

```bash
git clone https://github.com/DicksonK/pysetitup.git
cd pysetitup
./pysetitup.sh
```

The script will:
1. Check for Homebrew (install if needed)
2. Check for Python 3.10+ (install if needed)
3. Set up virtual environment
4. Launch the interactive TUI

### Option 2: Preview Mode (No Installation)

```bash
./pysetitup.sh --preview
```

Browse packages and test the interface without installing anything.

### Option 3: Custom Preset

```bash
./pysetitup.sh -f my-team-preset.yaml
```

Skip the preset selector and go straight to your custom configuration.

---

## Features

### 🎨 Interactive Package Selector

Beautiful terminal UI built with [Textual](https://textual.textualize.io/):

- **Search**: Press `/` to search packages by name or description
- **Categories**: Browse by CLI Tools, Development, Apps, etc.
- **Multi-select**: Space to toggle, Enter to confirm
- **Smart filtering**: Fuzzy search with relevance ranking
- **Keyboard shortcuts**: No mouse required

### 📦 Package Types Supported

| Type | Description | Examples |
|------|-------------|----------|
| **Homebrew Formulae** | CLI tools and libraries | git, node, python, ripgrep, fzf |
| **Homebrew Casks** | GUI applications | Visual Studio Code, iTerm2, Docker, Chrome |
| **npm Packages** | Global Node.js packages | typescript, eslint, prettier |
| **VS Code Extensions** | Editor extensions | Python, ESLint, Prettier extensions |

### ⚡ Smart Installation

- **Detects installed packages** - Shows what's already installed with versions
- **Parallel checking** - Checks all package managers simultaneously
- **Dry-run support** - Preview what will be installed
- **System checks** - Validates requirements before installation
- **Progress tracking** - Real-time progress for each package

### 🎯 Preset System

**Built-in Presets:**

- **Minimal** - Essential CLI tools (git, fzf, ripgrep, etc.)
- **Developer** - Full development setup (+ Node, Docker, VS Code, etc.)
- **Full** - Power user setup (+ Python, databases, cloud tools, etc.)

**Custom Presets:**

Create your own YAML presets:

```yaml
presets:
  my-team:
    name: "My Team Setup"
    description: "Company development environment"
    packages:
      - git
      - node
      - docker
    casks:
      - visual-studio-code
      - slack
    npm:
      - typescript
      - eslint
    vscode:
      - ms-python.python
      - dbaeumer.vscode-eslint
```

Then install with:
```bash
./pysetitup.sh -f team-preset.yaml
```

See [docs/user/CUSTOM_PRESETS.md](docs/user/CUSTOM_PRESETS.md) for full guide.

---

## Usage

### Basic Commands

```bash
# Interactive installation
./pysetitup.sh

# Preview mode (no installation)
./pysetitup.sh --preview

# Custom preset file
./pysetitup.sh -f my-preset.yaml

# Debug mode (pauses between screens)
./pysetitup.sh --debug

# Combine options
./pysetitup.sh --preview -f team-preset.yaml
```

### Python Direct Execution

```bash
# Production installer
uv run python install_packages.py
uv run python install_packages.py -f preset.yaml
uv run python install_packages.py --debug

# Preview mode
uv run python test_tui.py
uv run python test_tui.py -f preset.yaml
```

---

## Screenshots & Demo

### Preset Selection
Choose from curated presets or skip to manual selection:

```
┌─────────────────────────────────────────────────────────┐
│                   Select a Preset                       │
│   Choose a preset to get started quickly, or skip      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   MINIMAL   │  │  DEVELOPER  │  │    FULL     │    │
│  │ CLI tools   │  │ Full stack  │  │ Power users │    │
│  │ 12 packages │  │ 45 packages │  │ 87 packages │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────┤
│  [Install]  [Customize]  [Skip]                        │
└─────────────────────────────────────────────────────────┘
```

### Package Selection
Search, browse, and select packages:

```
┌─────────────────────────────────────────────────────────┐
│                  Package Selector                       │
│  Search: /ripgrep                                       │
├─────────────────────────────────────────────────────────┤
│  CLI Tools                                              │
│  ☑ git           - Version control system               │
│  ☑ ripgrep       - Fast text search tool                │
│  ☐ fzf           - Fuzzy finder                         │
│  ☐ jq            - JSON processor                       │
│                                                          │
│  Development                                            │
│  ☑ node          - JavaScript runtime                   │
│  ☐ python@3.12   - Python programming language          │
│                                                          │
│  Selected: 3 packages                                   │
└─────────────────────────────────────────────────────────┘
```

### Confirmation
Review before installation:

```
┌─────────────────────────────────────────────────────────┐
│           Package Installation Confirmation             │
│  Total: 15 packages | Already installed: 3 | To: 12    │
├─────────────────────────────────────────────────────────┤
│  Packages to install:                                   │
│    • docker                                             │
│    • ripgrep                                            │
│    • visual-studio-code                                 │
│                                                          │
│  Already installed (will be skipped):                   │
│    ✓ git (2.43.0)                                      │
│    ✓ node (21.5.0)                                     │
│                                                          │
│  Proceed with installation?                             │
│  [Y] Yes, Install  [N] No, Cancel  [Q] Quit            │
└─────────────────────────────────────────────────────────┘
```

---

## Architecture

### Tech Stack

- **Python 3.10+** - Modern async/await patterns
- **Textual** - TUI framework with rich widgets
- **Pydantic** - Type-safe configuration validation
- **uv** - Fast Python package installer
- **asyncio** - Parallel package checking and installation

### Project Structure

```
pysetitup/
├── brew/           # Homebrew client and installer
├── npm/            # npm client and installer
├── vscode/         # VS Code extension manager
├── config/         # Configuration loader and models
├── ui/             # TUI components (selector, confirmation, etc.)
├── installer/      # Installation orchestration
└── utils/          # Shared utilities (errors, logging, sorting)
```

### Key Features

- **Type-safe**: Full Pydantic validation for configs
- **Async-first**: Parallel operations throughout
- **Testable**: Comprehensive unit test coverage
- **Modular**: Clean separation of concerns
- **Extensible**: Easy to add new package managers

---

## Configuration

### Embedded Configuration

Built-in package database and presets are embedded in:
- `pysetitup/config/packages.yaml` - All available packages
- `pysetitup/config/presets.yaml` - Built-in presets

### Custom Presets

Create custom presets with full control:

```yaml
presets:
  data-science:
    name: "Data Science Setup"
    description: "Python ML/AI development environment"
    packages:
      - python@3.12
      - git
      - graphviz
    casks:
      - visual-studio-code
      - jupyter-notebook-viewer
    npm:
      - prettier
    vscode:
      - ms-python.python
      - ms-toolsai.jupyter
```

Features:
- **Override built-in presets** - Use same name to replace
- **Merge with embedded** - Custom presets extend available packages
- **Validate on load** - Pydantic ensures correctness
- **Share with team** - Version control and distribute

See full guide: [docs/user/CUSTOM_PRESETS.md](docs/user/CUSTOM_PRESETS.md)

---

## Development

### Prerequisites

- **macOS** 12.0 or later
- **Python** 3.10 or later
- **uv** - Fast Python package installer ([install](https://docs.astral.sh/uv/))

### Setup

```bash
# Clone repository
git clone https://github.com/DicksonK/pysetitup.git
cd pysetitup

# Create virtual environment
uv venv

# Install dependencies (editable mode)
uv pip install -e .

# Install dev dependencies
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
PYTHONPATH=. uv run pytest

# Run with coverage
PYTHONPATH=. uv run pytest --cov=pysetitup --cov-report=html

# Run specific test file
PYTHONPATH=. uv run pytest tests/unit/test_config_loader.py

# Run with verbose output
PYTHONPATH=. uv run pytest -v
```

### Code Quality

```bash
# Type checking
uv run mypy pysetitup

# Linting
uv run ruff check pysetitup

# Format code
uv run ruff format pysetitup
```

### Running Locally

```bash
# Preview mode (no installation)
./pysetitup.sh --preview

# Debug mode (pauses between screens)
./pysetitup.sh --debug

# Test custom preset
./pysetitup.sh --preview -f example-custom-preset.yaml

# Direct Python execution
PYTHONPATH=. uv run python test_tui.py
PYTHONPATH=. uv run python install_packages.py --help
```

---

## Documentation

### User Documentation

End-user guides in [docs/user/](docs/user/):

- **[Custom Presets](docs/user/CUSTOM_PRESETS.md)** - Create and use custom preset files
- **[Installation Scripts](docs/user/INSTALLATION_SCRIPTS.md)** - Installation guide
- **[TUI Overview](docs/user/README_TUI.md)** - Interactive package selector
- **[Quick Start](docs/user/QUICKSTART_TUI.md)** - Getting started guide
- **[Testing Guide](docs/user/TUI_TESTING_GUIDE.md)** - How to test the TUI

---

## Roadmap

### Current Status: v0.0.1 (Beta)

✅ **Completed:**
- Interactive TUI with search and filtering
- Homebrew formulae and casks support
- npm global packages support
- VS Code extensions support
- Custom preset file loading
- Parallel package checking
- Dry-run and preview modes
- Comprehensive test coverage

🚧 **In Progress:**
- Package publishing to PyPI
- Homebrew tap for easy installation
- Additional package managers (pip, cargo, gem)

🎯 **Planned:**
- Dotfiles management
- macOS preferences configuration
- Config import via web

---

## FAQ

**Q: Do I need anything installed first?**
A: Just macOS 12.0+ and Python 3.10+. The script will install Homebrew and uv if needed.

**Q: What if I already have some tools installed?**
A: PySetItUp detects them and shows their versions. You can skip reinstalling or update them.

**Q: Can I customize what gets installed?**
A: Yes! Choose a preset then customize, skip presets entirely, or load your own YAML file.

**Q: Does this work offline?**
A: Partially. The TUI works offline, but package installation requires internet.

**Q: Can I use this for team standardization?**
A: Absolutely! Create a team preset YAML file and share it in your repo.


---

## Contributing

Contributions welcome! Here's how to help:

### Bug Reports

Found a bug? [Open an issue](https://github.com/DicksonK/pysetitup/issues) with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System info (macOS version, Python version)

### Feature Requests

Have an idea? [Open an issue](https://github.com/DicksonK/pysetitup/issues) with:
- Clear description of the feature
- Use cases and examples
- Why it would be useful

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run tests and linting (`pytest`, `mypy`, `ruff`)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

See [docs/](docs/) for technical documentation.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built with:
- [Textual](https://textual.textualize.io/) - Amazing TUI framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer

Inspired by:
- [Homebrew Bundle](https://github.com/Homebrew/homebrew-bundle)
- [chezmoi](https://www.chezmoi.io/)
- [dotbot](https://github.com/anishathalye/dotbot)

---

<p align="center">
  Made with ❤️ for Mac developers
</p>

<p align="center">
  <a href="https://github.com/DicksonK/pysetitup">GitHub</a> ·
  <a href="https://github.com/DicksonK/pysetitup/issues">Issues</a> ·
  <a href="docs/">Documentation</a>
</p>

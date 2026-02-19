"""Pre-flight system checks UI with rich formatting."""


from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pysetitup.ui.terminal_check import MIN_TERMINAL_HEIGHT, MIN_TERMINAL_WIDTH


class SystemChecks:
    """
    Display pre-flight system checks with rich formatting.

    Parameters
    ----------
    console : Console, optional
        Rich console instance (creates new one if None)
    """

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.checks = []

    def add_check(self, name: str, status: str, message: str = "", required: bool = False) -> None:
        """
        Add a check result.

        Parameters
        ----------
        name : str
            Name of the check
        status : str
            Status: "pass", "fail", "warn", "skip"
        message : str, optional
            Additional message or details
        required : bool, default=False
            Whether this check is required to proceed
        """
        self.checks.append({"name": name, "status": status, "message": message, "required": required})

    def display(self, title: str = "System Checks") -> bool:
        """
        Display all checks in a formatted table.

        Parameters
        ----------
        title : str, default="System Checks"
            Title for the checks panel

        Returns
        -------
        bool
            True if all required checks passed, False otherwise
        """
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("Check", style="dim", width=30)
        table.add_column("Status", width=12)
        table.add_column("Details", no_wrap=False)

        all_required_passed = True

        for check in self.checks:
            name = check["name"]
            status = check["status"]
            message = check["message"]
            required = check["required"]

            # Status icon and color
            if status == "pass":
                status_text = Text("✓ PASS", style="bold green")
            elif status == "fail":
                status_text = Text("✗ FAIL", style="bold red")
                if required:
                    all_required_passed = False
            elif status == "warn":
                status_text = Text("⚠ WARN", style="bold yellow")
            elif status == "skip":
                status_text = Text("○ SKIP", style="dim")
            else:
                status_text = Text(f"? {status.upper()}", style="dim")

            # Add required indicator
            check_name = name
            if required:
                check_name = f"{name} *"

            table.add_row(check_name, status_text, message)

        # Display table in panel
        panel = Panel(
            table,
            title=f"[bold]{title}[/bold]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(panel)

        # Show legend if there are required checks
        if any(c["required"] for c in self.checks):
            self.console.print("[dim]* Required for installation[/dim]")

        return all_required_passed

    def clear(self) -> None:
        """Clear all checks."""
        self.checks = []


def check_homebrew() -> tuple[str, str]:
    """
    Check if Homebrew is installed.

    Returns
    -------
    tuple[str, str]
        (status, message) where status is "pass" or "fail"
    """
    import shutil

    if shutil.which("brew"):
        return ("pass", "Homebrew is installed")
    else:
        return ("fail", "Homebrew not found - install from https://brew.sh")


def check_git() -> tuple[str, str]:
    """
    Check if Git is installed.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    import shutil

    if shutil.which("git"):
        return ("pass", "Git is installed")
    else:
        return ("warn", "Git not found - will be installed")


def check_git_config() -> tuple[str, str]:
    """
    Check if Git is configured with user.name and user.email.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    import subprocess

    try:
        # Check if git user.name is set
        name_result = subprocess.run(
            ["git", "config", "--global", "user.name"], capture_output=True, text=True, timeout=5
        )

        # Check if git user.email is set
        email_result = subprocess.run(
            ["git", "config", "--global", "user.email"], capture_output=True, text=True, timeout=5
        )

        name = name_result.stdout.strip()
        email = email_result.stdout.strip()

        if name and email:
            return ("pass", f"Git configured: {name} <{email}>")
        elif name:
            return ("warn", "Git user.name set but missing user.email")
        elif email:
            return ("warn", "Git user.email set but missing user.name")
        else:
            return ("warn", "Git not configured - needs user.name and user.email")
    except Exception as e:
        return ("skip", f"Could not check Git config: {str(e)}")


def check_ssh_key() -> tuple[str, str]:
    """
    Check if SSH key exists for GitHub authentication.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    from pathlib import Path

    ssh_dir = Path.home() / ".ssh"

    # Check for common SSH key types
    ed25519_key = ssh_dir / "id_ed25519"
    rsa_key = ssh_dir / "id_rsa"

    if ed25519_key.exists():
        return ("pass", f"SSH key found: {ed25519_key}")
    elif rsa_key.exists():
        return ("pass", f"SSH key found: {rsa_key}")
    else:
        return ("warn", "No SSH key found - needed for GitHub authentication")


def check_vscode() -> tuple[str, str]:
    """
    Check if VS Code CLI is installed.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    import shutil

    if shutil.which("code"):
        return ("pass", "VS Code CLI is installed")
    else:
        return ("warn", "VS Code CLI not found - install via Command Palette")


def check_npm() -> tuple[str, str]:
    """
    Check if npm is installed.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    import shutil

    if shutil.which("npm"):
        return ("pass", "npm is installed")
    else:
        return ("warn", "npm not found - will be installed with Node.js")


def check_xcode_clt() -> tuple[str, str]:
    """
    Check if Xcode Command Line Tools are installed.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    import subprocess

    try:
        # Check if CLT is installed by checking xcode-select path
        result = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return ("pass", f"Xcode CLT installed at {result.stdout.strip()}")
        else:
            return ("fail", "Xcode Command Line Tools not installed")
    except Exception as e:
        return ("fail", f"Could not check Xcode CLT: {str(e)}")


def check_omz() -> tuple[str, str]:
    """
    Check if Oh My Zsh is installed.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    from pathlib import Path

    omz_path = Path.home() / ".oh-my-zsh"
    if omz_path.exists() and omz_path.is_dir():
        return ("pass", "Oh My Zsh is installed")
    else:
        return ("warn", "Oh My Zsh not installed")


def check_powerlevel10k() -> tuple[str, str]:
    """
    Check if Powerlevel10k theme is installed.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    from pathlib import Path

    # Check in Oh My Zsh custom themes directory
    omz_p10k = Path.home() / ".oh-my-zsh" / "custom" / "themes" / "powerlevel10k"
    # Check in standalone installation
    standalone_p10k = Path.home() / "powerlevel10k"

    if omz_p10k.exists() and omz_p10k.is_dir():
        return ("pass", "Powerlevel10k installed (Oh My Zsh)")
    elif standalone_p10k.exists() and standalone_p10k.is_dir():
        return ("pass", "Powerlevel10k installed (standalone)")
    else:
        return ("warn", "Powerlevel10k not installed")


def check_nerd_font() -> tuple[str, str]:
    """
    Check if a Nerd Font is installed.

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    import subprocess

    try:
        # List all installed fonts and check for Nerd Font patterns
        result = subprocess.run(["brew", "list", "--cask"], capture_output=True, text=True, timeout=10, check=False)

        if result.returncode != 0:
            return ("skip", "Could not check installed fonts")

        installed_casks = result.stdout.lower()

        # Check for common Nerd Fonts
        nerd_fonts = [
            "font-hack-nerd-font",
            "font-meslo-lg-nerd-font",
            "font-fira-code-nerd-font",
            "font-jetbrains-mono-nerd-font",
            "font-source-code-pro-nerd-font",
        ]

        for font in nerd_fonts:
            if font in installed_casks:
                # Extract font name
                font_name = font.replace("font-", "").replace("-nerd-font", "").title().replace("-", " ")
                return ("pass", f"Nerd Font installed: {font_name}")

        return ("warn", "No Nerd Font found - needed for Powerlevel10k icons")
    except Exception as e:
        return ("skip", f"Could not check Nerd Fonts: {str(e)}")


def check_terminal_size(min_width: int = MIN_TERMINAL_WIDTH, min_height: int = MIN_TERMINAL_HEIGHT) -> tuple[str, str]:
    """
    Check if terminal is large enough.

    Parameters
    ----------
    min_width : int
        Minimum required width in columns (default: MIN_TERMINAL_WIDTH from terminal_check)
    min_height : int
        Minimum required height in lines (default: MIN_TERMINAL_HEIGHT from terminal_check)

    Returns
    -------
    tuple[str, str]
        (status, message)
    """
    import shutil

    try:
        size = shutil.get_terminal_size()
        if size.columns >= min_width and size.lines >= min_height:
            return ("pass", f"Terminal size: {size.columns}×{size.lines}")
        else:
            msg = f"Terminal too small: {size.columns}×{size.lines} (need {min_width}×{min_height})"
            return ("fail", msg)
    except Exception:
        return ("skip", "Could not determine terminal size")


def run_system_checks(
    vscode_extensions: list[str],
    npm_packages: list[str],
    console: Console | None = None,
) -> bool:
    """
    Run all system checks and display results.

    Parameters
    ----------
    vscode_extensions : list[str]
        List of VS Code extension IDs to install
    npm_packages : list[str]
        List of npm packages to install
    console : Console, optional
        Rich console instance

    Returns
    -------
    bool
        True if all required checks passed
    """
    checks = SystemChecks(console)

    # Required checks
    status, msg = check_xcode_clt()
    checks.add_check("Xcode Command Line Tools", status, msg, required=True)

    status, msg = check_homebrew()
    checks.add_check("Homebrew", status, msg, required=True)

    status, msg = check_terminal_size()
    checks.add_check("Terminal Size", status, msg, required=True)

    # Git checks (optional but recommended)
    status, msg = check_git()
    checks.add_check("Git", status, msg, required=False)

    status, msg = check_git_config()
    checks.add_check("Git Configuration", status, msg, required=False)

    status, msg = check_ssh_key()
    checks.add_check("SSH Key (GitHub)", status, msg, required=False)

    # Shell environment checks
    status, msg = check_omz()
    checks.add_check("Oh My Zsh", status, msg, required=False)

    status, msg = check_powerlevel10k()
    checks.add_check("Powerlevel10k", status, msg, required=False)

    status, msg = check_nerd_font()
    checks.add_check("Nerd Font", status, msg, required=False)

    # VS Code check (required if extensions selected)
    if vscode_extensions:
        status, msg = check_vscode()
        checks.add_check("VS Code CLI", status, msg, required=True)

    # npm check (warn if packages selected)
    if npm_packages:
        status, msg = check_npm()
        checks.add_check("npm", status, msg, required=False)

    return checks.display()


def install_xcode_clt(console: Console | None = None) -> bool:
    """
    Install Xcode Command Line Tools.

    Parameters
    ----------
    console : Console, optional
        Rich console instance for output

    Returns
    -------
    bool
        True if installation succeeded
    """
    import subprocess

    if console is None:
        console = Console()

    console.print("\n[yellow]Installing Xcode Command Line Tools...[/yellow]")
    console.print("[dim]This will open a dialog. Please follow the prompts.[/dim]\n")

    try:
        # Trigger CLT installation dialog
        subprocess.run(["xcode-select", "--install"], check=False)
        console.print("\n[green]✓[/green] Xcode CLT installation dialog opened")
        console.print("[dim]Please complete the installation and press Enter to continue...[/dim]")
        input()
        return True
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to start Xcode CLT installation: {e}")
        return False


def install_omz(console: Console | None = None) -> bool:
    """
    Install Oh My Zsh.

    Parameters
    ----------
    console : Console, optional
        Rich console instance for output

    Returns
    -------
    bool
        True if installation succeeded
    """
    import subprocess

    if console is None:
        console = Console()

    console.print("\n[yellow]Installing Oh My Zsh...[/yellow]\n")

    try:
        # Download and run Oh My Zsh installer
        install_cmd = 'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'
        result = subprocess.run(install_cmd, shell=True, check=False)

        if result.returncode == 0:
            console.print("\n[green]✓[/green] Oh My Zsh installed successfully")
            return True
        else:
            console.print(f"\n[red]✗[/red] Oh My Zsh installation failed (exit code: {result.returncode})")
            return False
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to install Oh My Zsh: {e}")
        return False


def install_powerlevel10k(console: Console | None = None) -> bool:
    """
    Install Powerlevel10k theme for Oh My Zsh.

    Parameters
    ----------
    console : Console, optional
        Rich console instance for output

    Returns
    -------
    bool
        True if installation succeeded
    """
    import subprocess
    from pathlib import Path

    if console is None:
        console = Console()

    # Check if Oh My Zsh is installed first
    omz_path = Path.home() / ".oh-my-zsh"
    if not omz_path.exists():
        console.print("[red]✗[/red] Oh My Zsh is not installed. Please install it first.")
        return False

    console.print("\n[yellow]Installing Powerlevel10k theme...[/yellow]\n")

    try:
        # Clone Powerlevel10k into Oh My Zsh custom themes directory
        p10k_path = omz_path / "custom" / "themes" / "powerlevel10k"

        if p10k_path.exists():
            console.print("[dim]Powerlevel10k directory already exists, updating...[/dim]")
            result = subprocess.run(["git", "-C", str(p10k_path), "pull"], capture_output=True, text=True, check=False)
        else:
            result = subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth=1",
                    "https://github.com/romkatv/powerlevel10k.git",
                    str(p10k_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        if result.returncode == 0:
            console.print("[green]✓[/green] Powerlevel10k installed successfully")
            console.print('\n[dim]To activate, set ZSH_THEME="powerlevel10k/powerlevel10k" in ~/.zshrc[/dim]')
            return True
        else:
            console.print(f"[red]✗[/red] Powerlevel10k installation failed: {result.stderr}")
            return False
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to install Powerlevel10k: {e}")
        return False


def setup_git_config(console: Console | None = None) -> bool:
    """
    Guide user through Git configuration setup.

    Parameters
    ----------
    console : Console, optional
        Rich console instance for output

    Returns
    -------
    bool
        True if configuration succeeded
    """
    import subprocess

    if console is None:
        console = Console()

    console.print("\n[yellow]Setting up Git configuration...[/yellow]\n")

    try:
        # Get user name
        console.print("[cyan]Enter your full name (for Git commits):[/cyan]")
        name = input().strip()

        if not name:
            console.print("[red]✗[/red] Name cannot be empty")
            return False

        # Get user email
        console.print("[cyan]Enter your email address (for Git commits):[/cyan]")
        email = input().strip()

        if not email:
            console.print("[red]✗[/red] Email cannot be empty")
            return False

        # Set git config
        name_result = subprocess.run(
            ["git", "config", "--global", "user.name", name],
            capture_output=True,
            text=True,
            check=False,
        )

        email_result = subprocess.run(
            ["git", "config", "--global", "user.email", email],
            capture_output=True,
            text=True,
            check=False,
        )

        if name_result.returncode == 0 and email_result.returncode == 0:
            console.print("\n[green]✓[/green] Git configured successfully")
            console.print(f"[dim]Name: {name}[/dim]")
            console.print(f"[dim]Email: {email}[/dim]")
            return True
        else:
            console.print("[red]✗[/red] Failed to configure Git")
            return False
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to setup Git config: {e}")
        return False


def setup_github_ssh(console: Console | None = None) -> bool:
    """
    Guide user through GitHub SSH key setup with automated upload via gh CLI.

    This function:
    1. Authenticates with GitHub via gh CLI
    2. Generates SSH key locally
    3. Automatically uploads key to GitHub using gh CLI
    4. Adds key to ssh-agent

    Parameters
    ----------
    console : Console, optional
        Rich console instance for output

    Returns
    -------
    bool
        True if SSH key setup succeeded
    """
    import shutil
    import subprocess
    from pathlib import Path

    if console is None:
        console = Console()

    console.print("\n[yellow]Setting up GitHub SSH key...[/yellow]\n")

    # Check if gh CLI is installed
    if not shutil.which("gh"):
        console.print("[red]✗[/red] GitHub CLI (gh) is not installed")
        console.print("[dim]Install with: brew install gh[/dim]")
        return False

    try:
        # Step 1: Authenticate with GitHub
        console.print("[cyan]Step 1: Authenticating with GitHub...[/cyan]")
        console.print("[dim]You'll be prompted to authenticate via browser or token[/dim]\n")

        # Check if already authenticated
        auth_check = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=False)

        if auth_check.returncode != 0:
            # Need to authenticate
            console.print("[yellow]⚠[/yellow] Not authenticated with GitHub")
            auth_result = subprocess.run(["gh", "auth", "login", "-h", "github.com", "-p", "https", "-w"], check=False)

            if auth_result.returncode != 0:
                console.print("[red]✗[/red] GitHub authentication failed")
                return False

        console.print("[green]✓[/green] GitHub authentication successful\n")

        # Step 2: Check if SSH key already exists
        console.print("[cyan]Step 2: Checking for existing SSH keys...[/cyan]")
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(mode=0o700, exist_ok=True)

        ed25519_key = ssh_dir / "id_ed25519"
        rsa_key = ssh_dir / "id_rsa"

        if ed25519_key.exists() or rsa_key.exists():
            console.print("[yellow]⚠[/yellow] SSH key already exists")
            console.print("[cyan]Do you want to generate a new key? (y/N):[/cyan]")
            response = input().strip().lower()
            if response != "y":
                console.print("[dim]Using existing SSH key[/dim]\n")
                key_path = ed25519_key if ed25519_key.exists() else rsa_key
            else:
                key_path = None
        else:
            key_path = None

        # Step 3: Generate SSH key if needed
        if key_path is None:
            console.print("[cyan]Step 3: Generating SSH key...[/cyan]")
            console.print("[cyan]Enter your GitHub email address:[/cyan]")
            email = input().strip()

            if not email:
                console.print("[red]✗[/red] Email cannot be empty")
                return False

            console.print("[dim]Generating ed25519 SSH key...[/dim]")
            result = subprocess.run(
                ["ssh-keygen", "-t", "ed25519", "-C", email, "-f", str(ed25519_key), "-N", ""],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                console.print(f"[red]✗[/red] Failed to generate SSH key: {result.stderr}")
                return False

            key_path = ed25519_key
            console.print("[green]✓[/green] SSH key generated successfully\n")
        else:
            console.print("[green]✓[/green] Using existing SSH key\n")

        # Step 4: Add key to ssh-agent
        console.print("[cyan]Step 4: Adding key to ssh-agent...[/cyan]")
        subprocess.run(["ssh-add", "--apple-use-keychain", str(key_path)], check=False)
        console.print("[green]✓[/green] Key added to ssh-agent\n")

        # Step 5: Upload SSH key to GitHub using gh CLI
        console.print("[cyan]Step 5: Uploading SSH key to GitHub...[/cyan]")
        public_key_file = key_path.with_suffix(".pub")

        if not public_key_file.exists():
            console.print(f"[red]✗[/red] Public key file not found: {public_key_file}")
            return False

        # Use gh ssh-key add to upload the key
        upload_result = subprocess.run(
            ["gh", "ssh-key", "add", str(public_key_file), "--title", f"PySetItUp-{key_path.stem}"],
            capture_output=True,
            text=True,
            check=False,
        )

        if upload_result.returncode == 0:
            console.print("[green]✓[/green] SSH key successfully uploaded to GitHub!\n")
            console.print("[dim]You can now use SSH to authenticate with GitHub[/dim]")
            console.print(f"[dim]Key title: PySetItUp-{key_path.stem}[/dim]")
            return True
        else:
            # If upload failed, show manual instructions
            console.print(f"[yellow]⚠[/yellow] Automatic upload failed: {upload_result.stderr.strip()}")
            console.print("\n[yellow]Manual setup required:[/yellow]")

            with open(public_key_file) as f:
                public_key = f.read().strip()

            console.print("\n[cyan]Your SSH public key:[/cyan]\n")
            console.print(Panel(public_key, border_style="cyan"))
            console.print("\n[yellow]Next steps:[/yellow]")
            console.print("1. Copy the public key above")
            console.print("2. Go to: https://github.com/settings/keys")
            console.print("3. Click 'New SSH key'")
            console.print("4. Paste your key and save\n")
            return False

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to setup GitHub SSH: {e}")
        return False


def install_nerd_font(console: Console | None = None) -> bool:
    """
    Install a Nerd Font via Homebrew.

    Parameters
    ----------
    console : Console, optional
        Rich console instance for output

    Returns
    -------
    bool
        True if installation succeeded
    """
    import subprocess

    if console is None:
        console = Console()

    console.print("\n[yellow]Installing Nerd Font...[/yellow]\n")

    # Popular Nerd Font options
    font_options = [
        ("Hack Nerd Font", "font-hack-nerd-font"),
        ("Meslo LG Nerd Font", "font-meslo-lg-nerd-font"),
        ("JetBrains Mono Nerd Font", "font-jetbrains-mono-nerd-font"),
        ("Fira Code Nerd Font", "font-fira-code-nerd-font"),
        ("Source Code Pro Nerd Font", "font-source-code-pro-nerd-font"),
    ]

    console.print("[cyan]Choose a Nerd Font to install:[/cyan]\n")
    for i, (name, _) in enumerate(font_options, 1):
        console.print(f"  {i}. {name}")

    console.print("\n[cyan]Enter number (1-5) or press Enter for default (Hack):[/cyan]")
    choice = input().strip()

    # Default to Hack Nerd Font
    if not choice:
        choice = "1"

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(font_options):
            console.print("[red]✗[/red] Invalid choice")
            return False

        font_name, font_cask = font_options[idx]
        console.print(f"\n[dim]Installing {font_name}...[/dim]\n")

        result = subprocess.run(["brew", "install", "--cask", font_cask], check=False)

        if result.returncode == 0:
            console.print(f"\n[green]✓[/green] {font_name} installed successfully")
            console.print("\n[yellow]Important:[/yellow]")
            console.print("1. Restart your terminal application")
            console.print(f"2. Set your terminal font to '{font_name}'")
            console.print("3. Run 'p10k configure' to configure Powerlevel10k with the new font\n")
            return True
        else:
            console.print(f"\n[red]✗[/red] Failed to install {font_name}")
            return False
    except ValueError:
        console.print("[red]✗[/red] Invalid input. Please enter a number.")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to install Nerd Font: {e}")
        return False

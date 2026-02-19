"""Package sorting utilities."""

from pydantic import BaseModel, Field


class SortedPackages(BaseModel):
    """
    Type-safe container for sorted packages with validation.

    Attributes
    ----------
    packages : list[str]
        Sorted Homebrew formulae
    taps : list[str]
        Sorted Homebrew taps
    casks : list[str]
        Sorted Homebrew casks
    npm : list[str]
        Sorted npm packages
    vscode : list[str]
        Sorted VS Code extension IDs
    """

    packages: list[str] = Field(default_factory=list, description="Homebrew formulae")
    taps: list[str] = Field(default_factory=list, description="Homebrew taps")
    casks: list[str] = Field(default_factory=list, description="Homebrew casks")
    npm: list[str] = Field(default_factory=list, description="npm packages")
    vscode: list[str] = Field(default_factory=list, description="VS Code extension IDs")

    model_config = {"frozen": False}  # Allow modification after creation


def sort_packages(
    packages: list[str],
    taps: list[str],
    casks: list[str],
    npm: list[str],
    vscode: list[str],
) -> SortedPackages:
    """
    Sort all package lists alphabetically.

    Parameters
    ----------
    packages : list[str]
        Homebrew formulae to sort
    taps : list[str]
        Homebrew taps to sort
    casks : list[str]
        Homebrew casks to sort
    npm : list[str]
        npm packages to sort
    vscode : list[str]
        VS Code extension IDs to sort

    Returns
    -------
    SortedPackages
        Dictionary with all sorted lists

    Examples
    --------
    >>> sorted_pkgs = sort_packages(
    ...     packages=["zsh", "git", "fzf"],
    ...     taps=[],
    ...     casks=["warp", "cursor"],
    ...     npm=["typescript", "eslint"],
    ...     vscode=["ms-python.python"]
    ... )
    >>> sorted_pkgs.packages
    ['fzf', 'git', 'zsh']
    """
    return SortedPackages(
        packages=sorted(packages, key=str.lower),
        taps=sorted(taps, key=str.lower),
        casks=sorted(casks, key=str.lower),
        npm=sorted(npm, key=str.lower),
        vscode=sorted(vscode, key=str.lower),
    )


def get_installation_order() -> list[str]:
    """
    Get the installation order for package types.

    Returns
    -------
    list[str]
        Package types in installation order

    Notes
    -----
    The order is:
    1. packages (Homebrew formulae) - base tools
    2. taps (Homebrew taps) - required for some casks
    3. casks (Homebrew casks) - GUI applications
    4. npm (npm packages) - requires Node.js from packages
    5. vscode (VS Code extensions) - requires VS Code from casks
    """
    return ["packages", "taps", "casks", "npm", "vscode"]


def format_package_summary(sorted_packages: SortedPackages) -> str:
    """
    Format a human-readable summary of packages to install.

    Parameters
    ----------
    sorted_packages : SortedPackages
        Sorted package dictionary

    Returns
    -------
    str
        Formatted summary string

    Examples
    --------
    >>> pkgs = {
    ...     "packages": ["git", "fzf"],
    ...     "taps": [],
    ...     "casks": ["warp"],
    ...     "npm": ["typescript"],
    ...     "vscode": ["ms-python.python"]
    ... }
    >>> print(format_package_summary(pkgs))
    Packages (2): git, fzf
    Casks (1): warp
    npm (1): typescript
    VS Code (1): ms-python.python
    """
    lines = []

    for pkg_type in get_installation_order():
        items = getattr(sorted_packages, pkg_type)
        if not items:
            continue

        # Format label
        if pkg_type == "packages":
            label = "Packages"
        elif pkg_type == "taps":
            label = "Taps"
        elif pkg_type == "casks":
            label = "Casks"
        elif pkg_type == "npm":
            label = "npm"
        elif pkg_type == "vscode":
            label = "VS Code"
        else:
            label = pkg_type.title()

        # Format line
        count = len(items)
        items_str = ", ".join(items)
        lines.append(f"{label} ({count}): {items_str}")

    return "\n".join(lines)

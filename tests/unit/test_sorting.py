"""Unit tests for pysetitup.utils.sorting module."""

from pysetitup.utils.sorting import (
    SortedPackages,
    format_package_summary,
    get_installation_order,
    sort_packages,
)


class TestSortPackages:
    """Test sort_packages function."""

    def test_sort_packages_basic(self) -> None:
        """Test basic package sorting."""
        result = sort_packages(
            packages=["zsh", "git", "fzf"],
            taps=[],
            casks=["warp", "cursor"],
            npm=["typescript", "eslint"],
            vscode=["ms-python.python", "dbaeumer.vscode-eslint"],
        )

        assert result.packages == ["fzf", "git", "zsh"]
        assert result.casks == ["cursor", "warp"]
        assert result.npm == ["eslint", "typescript"]
        assert result.vscode == ["dbaeumer.vscode-eslint", "ms-python.python"]

    def test_sort_packages_empty(self) -> None:
        """Test sorting with empty lists."""
        result = sort_packages(packages=[], taps=[], casks=[], npm=[], vscode=[])

        assert result.packages == []
        assert result.casks == []
        assert result.npm == []
        assert result.vscode == []

    def test_sort_packages_case_insensitive(self) -> None:
        """Test case-insensitive sorting."""
        result = sort_packages(packages=["Zsh", "git", "FZF"], taps=[], casks=[], npm=[], vscode=[])

        assert result.packages == ["FZF", "git", "Zsh"]

    def test_sort_with_taps(self) -> None:
        """Test sorting with taps."""
        result = sort_packages(
            packages=[], taps=["homebrew/cask-versions", "homebrew/cask-fonts"], casks=[], npm=[], vscode=[]
        )

        assert result.taps == ["homebrew/cask-fonts", "homebrew/cask-versions"]


class TestGetInstallationOrder:
    """Test get_installation_order function."""

    def test_get_installation_order(self) -> None:
        """Test installation order."""
        order = get_installation_order()

        assert len(order) == 5
        assert order == ["packages", "taps", "casks", "npm", "vscode"]

    def test_packages_before_npm(self) -> None:
        """Test that packages come before npm."""
        order = get_installation_order()

        packages_idx = order.index("packages")
        npm_idx = order.index("npm")

        assert packages_idx < npm_idx

    def test_casks_before_vscode(self) -> None:
        """Test that casks come before vscode."""
        order = get_installation_order()

        casks_idx = order.index("casks")
        vscode_idx = order.index("vscode")

        assert casks_idx < vscode_idx

    def test_taps_before_casks(self) -> None:
        """Test that taps come before casks."""
        order = get_installation_order()

        taps_idx = order.index("taps")
        casks_idx = order.index("casks")

        assert taps_idx < casks_idx


class TestFormatPackageSummary:
    """Test format_package_summary function."""

    def test_format_package_summary_all_types(self) -> None:
        """Test formatting with all package types."""
        sorted_pkgs = SortedPackages(
            packages=["git", "fzf"],
            taps=["homebrew/cask-fonts"],
            casks=["warp"],
            npm=["typescript"],
            vscode=["ms-python.python"],
        )

        summary = format_package_summary(sorted_pkgs)

        assert "Packages (2): git, fzf" in summary
        assert "Taps (1): homebrew/cask-fonts" in summary
        assert "Casks (1): warp" in summary
        assert "npm (1): typescript" in summary
        assert "VS Code (1): ms-python.python" in summary

    def test_format_package_summary_skip_empty(self) -> None:
        """Test that empty lists are skipped."""
        sorted_pkgs = SortedPackages(packages=["git"], taps=[], casks=[], npm=[], vscode=[])

        summary = format_package_summary(sorted_pkgs)

        assert "Packages (1): git" in summary
        assert "Taps" not in summary
        assert "Casks" not in summary
        assert "npm" not in summary
        assert "VS Code" not in summary

    def test_format_package_summary_order(self) -> None:
        """Test that types appear in correct order."""
        sorted_pkgs = SortedPackages(
            packages=["git"], taps=["homebrew/tap"], casks=["warp"], npm=["typescript"], vscode=["ms-python.python"]
        )

        summary = format_package_summary(sorted_pkgs)
        lines = summary.split("\n")

        # Verify order
        assert lines[0].startswith("Packages")
        assert lines[1].startswith("Taps")
        assert lines[2].startswith("Casks")
        assert lines[3].startswith("npm")
        assert lines[4].startswith("VS Code")

    def test_format_package_summary_empty(self) -> None:
        """Test formatting with all empty lists."""
        sorted_pkgs = SortedPackages(packages=[], taps=[], casks=[], npm=[], vscode=[])

        summary = format_package_summary(sorted_pkgs)

        assert summary == ""

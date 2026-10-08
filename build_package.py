#!/usr/bin/env python3
"""Packaging script for Pac-Man 42.

Creates a standalone distribution package for deployment to public platforms
(e.g., itch.io or Steam unlisted/private builds), satisfying Chapter VII
of the 42 subject.
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def create_package() -> None:
    """Build a standalone release directory and zip archive for deployment."""
    root_dir = Path(__file__).parent.resolve()
    dist_dir = root_dir / "dist" / "pac-man-42"
    dist_root = root_dir / "dist"
    zip_path = root_dir / "dist" / "pac-man-42-release.zip"

    print("[*] Packaging Pac-Man 42 for distribution...")

    # Complie the package with the .whl extension
    print("[*] Building pac_man wheel package...")
    uv_cmd = shutil.which("uv")
    if uv_cmd:
        cmd = [uv_cmd, "build", "--wheel"]
    else:
        cmd = [sys.executable, "-m", "uv", "build", "--wheel"]

    subprocess.run(cmd, cwd=root_dir, check=True)

    # Clean and rebuild dist/pac-man-42
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Copy only .whl files in the wheels folder
    wheels_dir = dist_dir / "wheels"
    wheels_dir.mkdir(exist_ok=True)

    all_wheels = (
        list(dist_root.glob("pac_man-*.whl"))
        + list(root_dir.glob("*.whl"))
        + list(root_dir.glob("mlx-2.2/**/*.whl"))
    )
    for wheel in all_wheels:
        dest = wheels_dir / wheel.name
        shutil.copy(wheel, dest)
        print(f"    + {wheel.name}")

    # Copy documentation and configuration
    shutil.copy(root_dir / "config.json", dist_dir / "config.json")
    if (root_dir / "README.md").exists():
        shutil.copy(root_dir / "README.md", dist_dir / "README.md")

    # Start script for Linux/WSL and Windows
    launcher_sh = dist_dir / "launch.sh"
    launcher_sh.write_text(
        "#!/usr/bin/env bash\n"
        "set -e\n"
        'DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" '
        '>/dev/null 2>&1 && pwd )"\n'
        'cd "$DIR"\n\n'
        "# Crea la venv locale se non esiste\n"
        "if [ ! -d \".venv\" ]; then\n"
        "    python3 -m venv .venv\n"
        "fi\n\n"
        "# Attiva la venv e installa i wheels direttamente lì\n"
        "source .venv/bin/activate\n"
        "pip install --no-index --find-links=wheels mazegenerator mlx "
        "pac-man 2>/dev/null || \\\n"
        "pip install --find-links=wheels mazegenerator mlx pac-man\n\n"
        "# Avvia il gioco\n"
        "pac-man config.json\n",
        encoding="utf-8",
    )
    try:
        launcher_sh.chmod(0o755)
    except OSError:
        pass

    launcher_bat = dist_dir / "launch.bat"
    launcher_bat.write_text(
        "@echo off\r\n"
        "cd /d %~dp0\r\n"
        "if not exist \".venv\" (\r\n"
        "    python -m venv .venv\r\n"
        ")\r\n"
        "call .venv\\Scripts\\activate.bat\r\n"
        "pip install --no-index --find-links=wheels mazegenerator mlx "
        "pac-man 2>nul || "
        "pip install --find-links=wheels mazegenerator mlx pac-man\r\n"
        "pac-man config.json\r\n"
        "pause\r\n",
        encoding="utf-8",
    )

    # Create the ZIP file for itch.io
    if zip_path.exists():
        zip_path.unlink()

    print("[*] Creating release zip archive...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in dist_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(dist_dir.parent)
                zf.write(file, arcname)

    print(f"[OK] Package created successfully: {zip_path}")


if __name__ == "__main__":
    create_package()

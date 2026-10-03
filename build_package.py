#!/usr/bin/env python3
"""Packaging script for Pac-Man 42.

Creates a standalone distribution package for deployment to public platforms
(e.g., itch.io or Steam unlisted/private builds), satisfying Chapter VII
of the 42 subject.
"""

import shutil
import zipfile
from pathlib import Path


def create_package() -> None:
    """Build a standalone release directory and zip archive for deployment."""
    root_dir = Path(__file__).parent.resolve()
    dist_dir = root_dir / "dist" / "pac-man-42"
    zip_path = root_dir / "dist" / "pac-man-42-release.zip"

    print("📦 Packaging Pac-Man 42 for distribution...")

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy source code
    shutil.copytree(root_dir / "src", dist_dir / "src")

    # 2. Copy dependencies & wheels
    wheels = (
        list(root_dir.glob("*.whl"))
        + list(root_dir.glob("mlx-2.2/**/*.whl"))
    )
    wheels_dir = dist_dir / "wheels"
    wheels_dir.mkdir(exist_ok=True)
    for wheel in wheels:
        shutil.copy(wheel, wheels_dir / wheel.name)

    # 3. Copy configuration and assets
    shutil.copy(root_dir / "config.json", dist_dir / "config.json")
    shutil.copy(root_dir / "highscores.json", dist_dir / "highscores.json")
    shutil.copy(root_dir / "README.md", dist_dir / "README.md")
    shutil.copy(root_dir / "pac-man.py", dist_dir / "pac-man.py")

    # 4. Create in-package platform launcher & instructions
    launcher_sh = dist_dir / "launch.sh"
    launcher_sh.write_text(
        "#!/usr/bin/env bash\n"
        "python3 -m pip install --no-index "
        "--find-links=wheels mazegenerator mlx\n"
        "python3 pac-man.py config.json\n",
        encoding="utf-8",
    )
    launcher_sh.chmod(0o755)

    # 5. Compress into ZIP for Itch.io upload
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in dist_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(dist_dir.parent)
                zf.write(file, arcname)

    print("✅ Package created successfully:")
    print(f"   Directory: {dist_dir}")
    print(f"   Archive:   {zip_path}")


if __name__ == "__main__":
    create_package()

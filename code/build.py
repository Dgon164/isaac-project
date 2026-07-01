"""
Isaac — Build Executable

Usage:
    python build.py              # build as folder (faster startup)
    python build.py --onefile    # build as single .exe

Requirements:
    pip install flask numpy pyinstaller
    pip install pywebview        # optional, for native window
"""

import os
import sys
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
SEP = os.pathsep


def build():
    onefile = "--onefile" in sys.argv

    launcher = os.path.join(BASE, "launcher.py")
    templates = os.path.join(BASE, "templates")

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "Isaac",
        "--noconfirm",
        "--clean",
        # Bundle templates
        "--add-data", f"{templates}{SEP}templates",
        # Bundle isaac.py as a module
        "--add-data", f"{os.path.join(BASE, 'isaac.py')}{SEP}.",
        "--add-data", f"{os.path.join(BASE, 'app.py')}{SEP}.",
        # Hidden imports
        "--hidden-import", "flask",
        "--hidden-import", "numpy",
        "--hidden-import", "isaac",
        "--hidden-import", "app",
        # Output paths
        "--distpath", os.path.join(BASE, "dist"),
        "--workpath", os.path.join(BASE, "build"),
        "--specpath", os.path.join(BASE, "build"),
    ]

    if onefile:
        args.append("--onefile")
    else:
        args.append("--onedir")

    # Try to add webview as hidden import (optional)
    try:
        import webview
        args.extend(["--hidden-import", "webview"])
    except ImportError:
        pass

    # Icon (optional)
    icon = os.path.join(BASE, "isaac.ico")
    if os.path.exists(icon):
        args.extend(["--icon", icon])

    # Entry point
    args.append(launcher)

    print("Building Isaac...")
    print(f"  Mode: {'single file' if onefile else 'folder'}")
    print(f"  Entry: {launcher}")
    print()

    result = subprocess.run(args, cwd=BASE)

    if result.returncode == 0:
        if onefile:
            exe = os.path.join(BASE, "dist", "Isaac.exe" if os.name == "nt" else "Isaac")
        else:
            exe = os.path.join(BASE, "dist", "Isaac", "Isaac.exe" if os.name == "nt" else "Isaac")
        print(f"\n  Build complete: {exe}")
    else:
        print(f"\n  Build failed (exit code {result.returncode})")


if __name__ == "__main__":
    build()

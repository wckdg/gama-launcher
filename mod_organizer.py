"""
Mod Organizer - Creates Gama Launcher folder structure
Run this script to set up the directory tree
"""

import os
from pathlib import Path

def create_structure():
    """Create complete folder structure"""

    print("=" * 60)
    print("GAMA LAUNCHER - Folder Structure Creator")
    print("=" * 60)
    print()

    base_dir = Path.cwd()

    folders = [
        "runtime/java",
        "runtime/minecraft/versions",
        "runtime/minecraft/libraries",
        "runtime/minecraft/assets",
        "runtime/minecraft/mods",
        "mods/base",
        "mods/medium",
        "mods/heavy",
        "mods/ultimate",
        "shaderpacks",
        "config",
    ]

    print("Creating folders...")
    for folder in folders:
        folder_path = base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {folder}")

    print()
    print("=" * 60)
    print("FOLDER STRUCTURE CREATED!")
    print("=" * 60)
    print()
    print("Next steps:")
    print()
    print("1. Download all 34 mods from Modrinth (see MOD_DOWNLOAD_LIST.txt)")
    print("   and place them in the correct folders:")
    print()
    print("   mods/base/     ← 24 base mods (all tiers)")
    print("   mods/medium/   ← 4 visual mods (Medium+)")
    print("   mods/heavy/    ← 2 LOD mods (Heavy+)")
    print("   mods/ultimate/ ← 4 physics mods (Ultimate)")
    print()
    print("2. Download shader packs:")
    print("   shaderpacks/   ← ComplementaryReimagined_r5.6.1.zip")
    print("                    ComplementaryUnbound_r5.6.1.zip")
    print()
    print("3. (Optional) Copy mod configs to config/ folder")
    print()
    print("4. Build executable:")
    print("   python build.py")
    print()
    print("Folder structure:")
    print()
    for folder in folders:
        level = folder.count('/')
        indent = "  " * level
        name = folder.split('/')[-1]
        print(f"{indent}📁 {name}")
    print()

if __name__ == "__main__":
    create_structure()

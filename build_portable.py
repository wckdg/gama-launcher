# -*- coding: utf-8 -*-
"""
Build script - Creates Windows Portable ZIP
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

VERSION = "2.1.0"

print("📦 Building Gama Launcher Windows Portable")
print("="*50)

# Check if EXE already exists (from installer build)
exe_path = Path("dist") / "GamaLauncher.exe"

if not exe_path.exists():
    print("\n⚙️  EXE not found, building with PyInstaller...")
    
    # Clean old builds
    for d in ['build', 'dist']:
        if os.path.exists(d):
            shutil.rmtree(d)
    
    pyinstaller_args = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=GamaLauncher',
        '--icon=Logo.jpg',
        '--add-data=Logo.jpg;.',
        '--add-data=mods;mods',
        '--add-data=shaderpacks;shaderpacks',
        '--add-data=mod_lists.json;.',
        # Hidden imports
        '--hidden-import=customtkinter',
        '--hidden-import=PIL',
        '--hidden-import=psutil',
        '--hidden-import=GPUtil',
        '--hidden-import=requests',
        '--hidden-import=json',
        '--hidden-import=urllib3',
        '--hidden-import=certifi',
        'launcher.py'
    ]
    
    # Check if assets exist and add them
    if Path("assets").exists():
        print("  ✓ Found assets/ folder - will be included")
        pyinstaller_args.insert(-1, '--add-data=assets;assets')
    
    try:
        subprocess.run(pyinstaller_args, check=True)
        print("✅ EXE built successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        sys.exit(1)
else:
    print("\n✓ Using existing EXE from dist/")

# Create portable structure
print("\n📦 Creating portable package...")

portable_name = f"GamaLauncher-Portable-v{VERSION}"
portable_dir = Path("dist") / portable_name

# Clean old portable if exists
if portable_dir.exists():
    shutil.rmtree(portable_dir)

portable_dir.mkdir(parents=True, exist_ok=True)

# Copy EXE
print("   • Copying executable...")
shutil.copy2(exe_path, portable_dir / "GamaLauncher.exe")

# Copy Logo
print("   • Copying logo...")
if Path("Logo.jpg").exists():
    shutil.copy2("Logo.jpg", portable_dir / "Logo.jpg")

# Copy mods
print("   • Copying mods...")
if Path("mods").exists():
    shutil.copytree("mods", portable_dir / "mods")
else:
    print("     ⚠️  No mods folder found!")

# Copy shaderpacks
print("   • Copying shaderpacks...")
if Path("shaderpacks").exists():
    shutil.copytree("shaderpacks", portable_dir / "shaderpacks")
else:
    print("     ⚠️  No shaderpacks folder found!")

# Copy mod_lists.json
print("   • Copying config...")
if Path("mod_lists.json").exists():
    shutil.copy2("mod_lists.json", portable_dir / "mod_lists.json")
else:
    print("     ⚠️  No mod_lists.json found!")

# Copy assets if they exist
assets_included = False
if Path("assets").exists():
    print("   • Copying assets (~400MB, may take a moment)...")
    shutil.copytree("assets", portable_dir / "assets")
    assets_included = True
    print("     ✓ Assets included")
else:
    print("   • No assets folder (users will download on first launch)")

# Create README.txt
print("   • Creating README...")
readme_content = f"""GAMA LAUNCHER v{VERSION} - PORTABLE EDITION
{'='*60}

QUICK START:
1. Run GamaLauncher.exe
2. Enter your Minecraft username
3. Select quality preset
4. Click LAUNCH GAME

FEATURES:
• No installation required
• Includes all mods and shaderpacks
{'• Pre-downloaded game assets (~400MB)' if assets_included else '• Assets will download on first launch'}
• Automatic Java 17 download
• Automatic Minecraft + Fabric installation
• Quality presets: Very Low to Ultra
• Optional shader support

SYSTEM REQUIREMENTS:
• Windows 10/11 64-bit
• 4GB RAM minimum (8GB+ recommended for shaders)
• ~2GB free disk space (more for game files)

SERVER:
• Name: GAMA KLUB
• IP: gamaklub.ggwp.cc
• Automatically added to multiplayer list

PORTABLE MODE:
This is a portable version. All files (Minecraft, Java, saves, etc.)
will be stored in the "runtime" folder next to the executable.

You can move the entire folder to another location or USB drive.

SUPPORT:
• Discord: [Your Discord]
• GitHub: https://github.com/wckdg/gama-launcher

{'='*60}
Enjoy the game!
"""

with open(portable_dir / "README.txt", 'w', encoding='utf-8') as f:
    f.write(readme_content)

# Create ZIP
print("\n📦 Creating ZIP archive...")
zip_name = f"{portable_name}.zip"
zip_path = Path("dist") / zip_name

# Remove old ZIP if exists
if zip_path.exists():
    os.remove(zip_path)

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(portable_dir):
        for file in files:
            file_path = Path(root) / file
            arcname = file_path.relative_to(portable_dir.parent)
            zipf.write(file_path, arcname)
            
            # Show progress for large files
            if file_path.stat().st_size > 10 * 1024 * 1024:  # > 10MB
                print(f"     Compressing: {file_path.name}...")

zip_size = zip_path.stat().st_size / (1024*1024)

# Calculate total size
total_size = sum(f.stat().st_size for f in portable_dir.rglob('*') if f.is_file())
total_size_mb = total_size / (1024*1024)

print("\n" + "="*60)
print("✅ PORTABLE BUILD COMPLETE!")
print("="*60)
print(f"\n📂 Created:")
print(f"  • {zip_path}")
print(f"\n📊 Sizes:")
print(f"  Uncompressed: {total_size_mb:.1f} MB")
print(f"  ZIP archive: {zip_size:.1f} MB")
print(f"  Compression: {(1 - zip_size/total_size_mb)*100:.1f}%")

print("\n💡 Portable ZIP includes:")
print("  ✓ Launcher executable")
print("  ✓ All mods (base/medium/heavy/ultimate)")
print("  ✓ All shaderpacks")

if assets_included:
    print("  ✓ Pre-downloaded assets (~400MB)")
else:
    print("  ⚠️  No assets (users will download on first launch)")

print("  ✓ README.txt")

print("\n📝 Usage:")
print("  1. Extract ZIP to any folder")
print("  2. Run GamaLauncher.exe")
print("  3. Everything stored in 'runtime' subfolder")

print("\n🎉 Ready to distribute!")
print("="*60)

# Clean up portable folder (keep only ZIP)
print("\n🧹 Cleaning up temporary files...")
shutil.rmtree(portable_dir)
print("  ✓ Temporary folder removed")

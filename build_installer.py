# -*- coding: utf-8 -*-
"""
Build script - Creates Windows Installer with Inno Setup
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

VERSION = "2.1.0"

print("🪟 Building Gama Launcher Windows Installer")
print("="*50)

# Clean old builds
print("\n🧹 Cleaning old builds...")
for d in ['build', 'dist']:
    if os.path.exists(d):
        shutil.rmtree(d)
        print(f"  ✓ Removed {d}/")

# Build EXE with PyInstaller
print("\n⚙️  Building EXE with PyInstaller...")

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
else:
    print("  ⚠️  No assets/ folder found (run download_assets.py first)")

try:
    subprocess.run(pyinstaller_args, check=True)
    print("✅ EXE built successfully!")
except subprocess.CalledProcessError as e:
    print(f"❌ PyInstaller failed: {e}")
    sys.exit(1)

# Check if EXE was created
exe_path = Path("dist") / "GamaLauncher.exe"
if not exe_path.exists():
    print(f"❌ EXE not found at {exe_path}")
    sys.exit(1)

exe_size = exe_path.stat().st_size / (1024*1024)
print(f"  ✓ EXE size: {exe_size:.1f} MB")

# Create installer with Inno Setup
print("\n📦 Creating installer with Inno Setup...")

# Check if Inno Setup is installed
inno_setup_path = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
if not inno_setup_path.exists():
    # Try alternate path
    inno_setup_path = Path(r"C:\Program Files\Inno Setup 6\ISCC.exe")

if not inno_setup_path.exists():
    print("❌ Inno Setup not found!")
    print("   Install from: https://jrsoftware.org/isdl.php")
    print(f"\n📂 EXE available at: {exe_path}")
    sys.exit(1)

# Check if installer.iss exists
iss_file = Path("installer.iss")
if not iss_file.exists():
    print("❌ installer.iss not found!")
    print(f"\n📂 EXE available at: {exe_path}")
    sys.exit(1)

try:
    result = subprocess.run(
        [str(inno_setup_path), str(iss_file)],
        check=True,
        capture_output=True,
        text=True
    )
    print("✅ Installer created successfully!")
except subprocess.CalledProcessError as e:
    print(f"❌ Inno Setup failed!")
    print(f"   Error: {e.stderr}")
    print(f"\n📂 EXE available at: {exe_path}")
    sys.exit(1)

# Find the installer
installer_path = Path("dist") / f"GamaLauncher-Setup-v{VERSION}.exe"
if not installer_path.exists():
    # Try without version
    installer_path = Path("dist") / "GamaLauncher-Setup.exe"

if installer_path.exists():
    installer_size = installer_path.stat().st_size / (1024*1024)
    
    print("\n" + "="*60)
    print("✅ BUILD COMPLETE!")
    print("="*60)
    print(f"\n📂 Files created:")
    print(f"  • {exe_path} ({exe_size:.1f} MB)")
    print(f"  • {installer_path} ({installer_size:.1f} MB)")
    
    print("\n💡 Installer includes:")
    print("  ✓ Launcher executable")
    print("  ✓ All mods (base/medium/heavy/ultimate)")
    print("  ✓ All shaderpacks")
    
    if Path("assets").exists():
        print("  ✓ Pre-downloaded assets (~400MB)")
    else:
        print("  ⚠️  No assets (users will download on first launch)")
    
    print("  ✓ Start menu shortcuts")
    print("  ✓ Desktop shortcut option")
    print("  ✓ Uninstaller")
    
    print("\n🎉 Ready to distribute!")
    print("="*60)
else:
    print(f"\n⚠️  Installer not found at expected location")
    print(f"📂 EXE available at: {exe_path}")

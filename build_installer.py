"""
Build script - Creates Windows installer with Inno Setup
FIXED: Adds --hidden-import=requests for Minecraft downloads
"""

import os
import shutil
import subprocess
from pathlib import Path

VERSION = "2.1.0"

print("🚀 Building Gama Launcher Installer")
print("="*50)

# Clean old builds
print("\n🧹 Cleaning old builds...")
for d in ['build', 'dist', '__pycache__']:
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
    '--icon=icon.ico',
    '--add-data=Logo.jpg;.',
    # Hidden imports (FIXED: added requests and json)
    '--hidden-import=customtkinter',
    '--hidden-import=PIL',
    '--hidden-import=psutil',
    '--hidden-import=GPUtil',
    '--hidden-import=requests',      # NEW: For Minecraft/Fabric downloads
    '--hidden-import=json',          # NEW: For config handling
    '--hidden-import=urllib3',       # NEW: Requests dependency
    '--hidden-import=certifi',       # NEW: SSL certificates for HTTPS
    'launcher.py'
]

try:
    subprocess.run(pyinstaller_args, check=True)
    print("✅ EXE built successfully!")
except subprocess.CalledProcessError as e:
    print(f"❌ PyInstaller failed: {e}")
    input("\nPress Enter to exit...")
    exit(1)

# Check for Inno Setup
print("\n🔍 Looking for Inno Setup...")
inno_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not os.path.exists(inno_path):
    print("\n❌ Inno Setup not found!")
    print("\n📥 Please install Inno Setup:")
    print("   1. Download: https://jrsoftware.org/isdl.php")
    print("   2. Install to default location")
    print("   3. Run this script again")
    print("\n📂 Files created:")
    print("   • dist/GamaLauncher.exe (standalone)")
    input("\nPress Enter to exit...")
    exit(1)

# Create installer with Inno Setup
print("\n📦 Creating installer with Inno Setup...")

try:
    inno_args = [
        inno_path,
        'installer.iss',
        f'/DMyAppVersion={VERSION}'
    ]
    subprocess.run(inno_args, check=True)
    print("✅ Installer created successfully!")
except subprocess.CalledProcessError as e:
    print(f"❌ Inno Setup failed: {e}")
    input("\nPress Enter to exit...")
    exit(1)

# Show results
print("\n" + "="*60)
print("✅ BUILD COMPLETE!")
print("="*60)

print("\n📂 Files created:")
print(f"   • dist/GamaLauncher.exe (standalone)")
print(f"   • dist/GamaLauncher-Setup-v{VERSION}.exe (installer)")

# Show sizes
exe_path = Path("dist/GamaLauncher.exe")
setup_path = Path(f"dist/GamaLauncher-Setup-v{VERSION}.exe")

if exe_path.exists():
    exe_size = exe_path.stat().st_size / (1024*1024)
    print(f"\n📊 Sizes:")
    print(f"   Standalone EXE: {exe_size:.1f} MB")

if setup_path.exists():
    setup_size = setup_path.stat().st_size / (1024*1024)
    print(f"   Installer: {setup_size:.1f} MB")

print("\n🎉 Ready to distribute!")
print("\n💡 Installer includes:")
print("   ✓ Launcher EXE")
print("   ✓ All mods (base/medium/heavy/ultimate)")
print("   ✓ All shaderpacks")
print("   ✓ Config files")
print("   ✓ Desktop shortcut (optional)")
print("   ✓ Start menu entry")
print("   ✓ Uninstaller")

print("\n" + "="*60)
input("\nPress Enter to exit...")

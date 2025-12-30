# -*- coding: utf-8 -*-
"""
Build script - Creates macOS .app and DMG
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

VERSION = "2.1.0"

print("🍎 Building Gama Launcher for macOS")
print("="*50)

# Clean old builds
print("\n🧹 Cleaning old builds...")
for d in ['build', 'dist', '__pycache__']:
    if os.path.exists(d):
        shutil.rmtree(d)
        print(f"  ✓ Removed {d}/")

# Check if icon.icns exists, create if not
if not Path("icon.icns").exists():
    print("\n📝 Creating icon.icns from Logo.jpg...")
    try:
        subprocess.run(['mkdir', '-p', 'icon.iconset'], check=True)
        
        # Create different sizes
        sizes = [16, 32, 128, 256, 512]
        for size in sizes:
            subprocess.run([
                'sips', '-z', str(size), str(size), 
                'Logo.jpg', '--out', 
                f'icon.iconset/icon_{size}x{size}.png'
            ], capture_output=True)
        
        # Create .icns
        subprocess.run(['iconutil', '-c', 'icns', 'icon.iconset', '-o', 'icon.icns'], 
                      capture_output=True)
        
        # Cleanup
        shutil.rmtree('icon.iconset', ignore_errors=True)
        print("  ✓ Created icon.icns")
    except Exception as e:
        print(f"  ⚠️  Could not create icon.icns: {e}")
        # Create empty file so build doesn't fail
        Path("icon.icns").touch()

# Build with PyInstaller
print("\n⚙️  Building macOS app with PyInstaller...")

pyinstaller_args = [
    'pyinstaller',
    '--onedir',  # Changed from --onefile for better compatibility
    '--windowed',
    '--name=GamaLauncher',
    '--icon=icon.icns',
    '--add-data=Logo.jpg:.',
    '--add-data=mods:mods',
    '--add-data=shaderpacks:shaderpacks',
    '--add-data=mod_lists.json:.',
    '--osx-bundle-identifier=com.gamaklub.launcher',
    '--target-architecture=universal2',  # Works on Intel + Apple Silicon
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

try:
    subprocess.run(pyinstaller_args, check=True)
    print("✅ App built successfully!")
except subprocess.CalledProcessError as e:
    print(f"❌ PyInstaller failed: {e}")
    sys.exit(1)

# Get paths
dist_dir = Path("dist")
app_dir = dist_dir / "GamaLauncher.app"

if not app_dir.exists():
    print(f"❌ App not found at {app_dir}")
    sys.exit(1)

# Create Info.plist
print("\n📝 Creating Info.plist...")
info_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>GamaLauncher</string>
    <key>CFBundleIdentifier</key>
    <string>com.gamaklub.launcher</string>
    <key>CFBundleName</key>
    <string>Gama Launcher</string>
    <key>CFBundleDisplayName</key>
    <string>Gama Launcher</string>
    <key>CFBundleVersion</key>
    <string>{VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>{VERSION}</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
"""

info_plist_path = app_dir / "Contents" / "Info.plist"
with open(info_plist_path, 'w') as f:
    f.write(info_plist_content)
print("  ✓ Info.plist created")

# Check if create-dmg is installed
print("\n🔍 Checking for create-dmg...")
try:
    subprocess.run(['which', 'create-dmg'], check=True, capture_output=True)
    print("  ✓ create-dmg found")
except subprocess.CalledProcessError:
    print("  ⚠️  create-dmg not found. Installing with Homebrew...")
    try:
        subprocess.run(['brew', 'install', 'create-dmg'], check=True)
    except subprocess.CalledProcessError:
        print("  ❌ Could not install create-dmg")
        print("\n📂 App created at: dist/GamaLauncher.app")
        print("  You can manually create DMG later")
        sys.exit(1)

# Create DMG
print("\n📦 Creating DMG installer...")
dmg_name = f"GamaLauncher-v{VERSION}-macOS.dmg"
dmg_path = dist_dir / dmg_name

# Remove old DMG if exists
if dmg_path.exists():
    os.remove(dmg_path)

try:
    subprocess.run([
        'create-dmg',
        '--volname', f'Gama Launcher {VERSION}',
        '--volicon', 'icon.icns',
        '--window-pos', '200', '120',
        '--window-size', '600', '400',
        '--icon-size', '100',
        '--icon', 'GamaLauncher.app', '175', '120',
        '--hide-extension', 'GamaLauncher.app',
        '--app-drop-link', '425', '120',
        str(dmg_path),
        str(app_dir)
    ], check=True)
    print("✅ DMG created successfully!")
except subprocess.CalledProcessError as e:
    print(f"❌ DMG creation failed: {e}")
    print("\n📂 App available at: dist/GamaLauncher.app")
    sys.exit(1)

# Show results
print("\n" + "="*60)
print("✅ BUILD COMPLETE!")
print("="*60)
print(f"\n📂 Files created:")
print(f"  • dist/GamaLauncher.app (app bundle)")
print(f"  • dist/{dmg_name} (installer)")

# Show sizes
app_size = sum(f.stat().st_size for f in app_dir.rglob('*') if f.is_file()) / (1024*1024)
if dmg_path.exists():
    dmg_size = dmg_path.stat().st_size / (1024*1024)
    print(f"\n📊 Sizes:")
    print(f"  App Bundle: {app_size:.1f} MB")
    print(f"  DMG Installer: {dmg_size:.1f} MB")

print("\n🎉 Ready to distribute!")
print("\n💡 DMG includes:")
print("  ✓ Launcher app")
print("  ✓ All mods (base/medium/heavy/ultimate)")
print("  ✓ All shaderpacks")
print("  ✓ Config files")
print("  ✓ Drag-to-install interface")

print("\n" + "="*60)

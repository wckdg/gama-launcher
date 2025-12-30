"""
Build script for macOS - Creates .app bundle and DMG
NEW: macOS support for Gama Launcher
"""

import os
import shutil
import subprocess
from pathlib import Path
import sys

VERSION = "2.1.0"

print("🍎 Building Gama Launcher for macOS")
print("="*50)

# Check if running on macOS
if sys.platform != "darwin":
    print("❌ This script must be run on macOS!")
    print(f"   Current platform: {sys.platform}")
    print("\n💡 For Windows, use build_installer.py")
    exit(1)

# Clean old builds
print("\n🧹 Cleaning old builds...")
for d in ['build', 'dist', '__pycache__']:
    if os.path.exists(d):
        shutil.rmtree(d)
        print(f"  ✓ Removed {d}/")

# Build .app with PyInstaller
print("\n⚙️  Building .app with PyInstaller...")

pyinstaller_args = [
    'pyinstaller',
    '--onefile',
    '--windowed',
    '--name=GamaLauncher',
    '--icon=icon.icns',  # macOS icon (you'll need to create this)
    '--add-data=Logo.jpg:.',
    # Hidden imports
    '--hidden-import=customtkinter',
    '--hidden-import=PIL',
    '--hidden-import=psutil',
    '--hidden-import=requests',
    '--hidden-import=json',
    '--hidden-import=urllib3',
    '--hidden-import=certifi',
    # macOS specific
    '--osx-bundle-identifier=com.gamaserver.launcher',
    'launcher.py'
]

try:
    subprocess.run(pyinstaller_args, check=True)
    print("✅ .app bundle built successfully!")
except subprocess.CalledProcessError as e:
    print(f"❌ PyInstaller failed: {e}")
    print("\n💡 Make sure you have PyInstaller installed:")
    print("   pip install pyinstaller")
    exit(1)

# Check if .app was created
app_path = Path("dist/GamaLauncher.app")
if not app_path.exists():
    print("❌ GamaLauncher.app not found in dist/")
    exit(1)

print(f"✅ Found: {app_path}")

# Create Resources folder inside .app
print("\n📦 Adding resources to .app bundle...")
resources_dir = app_path / "Contents" / "Resources"
resources_dir.mkdir(parents=True, exist_ok=True)

# Copy mods
if Path("mods").exists():
    print("   • Copying mods...")
    mods_dest = resources_dir / "mods"
    if mods_dest.exists():
        shutil.rmtree(mods_dest)
    shutil.copytree("mods", mods_dest)
    mod_count = sum(1 for _ in mods_dest.rglob("*.jar"))
    print(f"     ✓ Copied {mod_count} mods")

# Copy shaderpacks
if Path("shaderpacks").exists():
    print("   • Copying shaderpacks...")
    shaders_dest = resources_dir / "shaderpacks"
    if shaders_dest.exists():
        shutil.rmtree(shaders_dest)
    shutil.copytree("shaderpacks", shaders_dest)
    shader_count = sum(1 for _ in shaders_dest.rglob("*.zip"))
    print(f"     ✓ Copied {shader_count} shaderpacks")

# Copy config
if Path("mod_lists.json").exists():
    print("   • Copying mod_lists.json...")
    shutil.copy("mod_lists.json", resources_dir)

# Create README for macOS
print("   • Creating README...")
readme_content = f"""
╔═══════════════════════════════════════════════════════════════╗
║          GAMA LAUNCHER v{VERSION} - macOS EDITION              ║
╚═══════════════════════════════════════════════════════════════╝

📦 INSTALLATION:

1. Drag GamaLauncher.app to your Applications folder
2. Double-click to run
3. If macOS blocks it (unsigned app):
   • Right-click → Open
   • Or: System Settings → Privacy & Security → Open Anyway

🚀 HOW TO USE:

1. Launch GamaLauncher
2. Select your quality preset
3. Enable shaders if desired (Medium and above)
4. Enter your Minecraft username
5. Click "LAUNCH GAME"

📁 FILE LOCATIONS:

• Application: /Applications/GamaLauncher.app
• Game files: ~/Library/Application Support/GamaLauncher
• Logs: ~/Library/Application Support/GamaLauncher/runtime/minecraft/logs

💡 IMPORTANT NOTES:

• First launch downloads Java for macOS (~200MB)
• First launch takes 2-4 minutes to load all mods
• macOS may ask for permissions - allow them
• Java 17 is downloaded automatically (no manual install needed)

⚙️  SYSTEM REQUIREMENTS:

┌─────────────┬─────────┬──────────────────────────────────────┐
│ Preset      │ RAM     │ Hardware Requirements                │
├─────────────┼─────────┼──────────────────────────────────────┤
│ Very Low    │ 4GB     │ Any Mac, Intel or Apple Silicon      │
│ Low         │ 6GB     │ Any Mac with 8GB+ RAM                │
│ Medium      │ 8-10GB  │ Mac with dedicated GPU (shaders)     │
│ High        │ 10-12GB │ Mac with M1/M2 or Intel + GPU        │
│ Very High   │ 12-14GB │ M1 Pro/Max or Intel with 16GB RAM    │
│ Ultra       │ 16-18GB │ M2 Pro/Max/Ultra or Intel + 32GB     │
└─────────────┴─────────┴──────────────────────────────────────┘

Note: Apple Silicon Macs (M1/M2/M3) run Java via Rosetta

🎨 SHADER SUPPORT:

• Very Low / Low: No shaders (performance focus)
• Medium / High: Complementary Reimagined (optional)
• Very High: Complementary Reimagined + Distant Horizons
• Ultra: Complementary Unbound (best quality)

🔧 TROUBLESHOOTING:

• "App is damaged": 
  sudo xattr -rd com.apple.quarantine /Applications/GamaLauncher.app

• Permission denied:
  Right-click app → Open (instead of double-click)

• No sound: Wait for first-launch asset download to complete

• Performance: Try lower preset or disable shaders

• Java download fails: Check internet connection

═══════════════════════════════════════════════════════════════

Made with ❤️  for Gama Server Community

═══════════════════════════════════════════════════════════════
"""

(resources_dir / "README.txt").write_text(readme_content, encoding='utf-8')

# Create DMG (if create-dmg is installed)
print("\n💿 Creating DMG installer...")

dmg_name = f"GamaLauncher-v{VERSION}-macOS.dmg"
dmg_path = Path("dist") / dmg_name

# Check if create-dmg is installed
try:
    subprocess.run(['which', 'create-dmg'], check=True, capture_output=True)
    has_create_dmg = True
except subprocess.CalledProcessError:
    has_create_dmg = False

if has_create_dmg:
    # Remove old DMG if exists
    if dmg_path.exists():
        dmg_path.unlink()
    
    create_dmg_cmd = [
        'create-dmg',
        '--volname', f'GAMA Launcher {VERSION}',
        '--volicon', 'icon.icns',
        '--window-pos', '200', '120',
        '--window-size', '600', '400',
        '--icon-size', '100',
        '--icon', 'GamaLauncher.app', '175', '190',
        '--hide-extension', 'GamaLauncher.app',
        '--app-drop-link', '425', '190',
        str(dmg_path),
        'dist/'
    ]
    
    try:
        subprocess.run(create_dmg_cmd, check=True)
        print(f"✅ DMG created: {dmg_name}")
    except subprocess.CalledProcessError:
        print("⚠️  DMG creation failed, but .app is ready")
else:
    print("⚠️  'create-dmg' not installed")
    print("   Install it with: brew install create-dmg")
    print("   Or distribute the .app directly")

# Show results
print("\n" + "="*60)
print("✅ macOS BUILD COMPLETE!")
print("="*60)

print("\n📂 Files created:")
print(f"   • dist/GamaLauncher.app (macOS application)")

if dmg_path.exists():
    print(f"   • dist/{dmg_name} (DMG installer)")
    dmg_size = dmg_path.stat().st_size / (1024*1024)
    print(f"\n📊 DMG Size: {dmg_size:.1f} MB")

# Show app size
if app_path.exists():
    app_size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file()) / (1024*1024)
    print(f"📊 App Size: {app_size:.1f} MB")

print("\n🎉 Ready to distribute!")
print("\n💡 Distribution options:")
print("   1. Share the DMG file (recommended)")
print("   2. Zip the .app and share")
print("   3. Upload to GitHub Releases")
print("\n⚠️  Note: App is unsigned - users need to:")
print("   • Right-click → Open (first launch)")
print("   • Or disable Gatekeeper temporarily")

print("\n📝 To code-sign (optional, requires Apple Developer account):")
print("   codesign --deep --force --verify --verbose \\")
print("     --sign 'Developer ID Application: Your Name' \\")
print("     dist/GamaLauncher.app")

print("\n" + "="*60)

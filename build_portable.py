"""
Build portable ZIP - with all mods and shaders
UPDATED: New tier names and version 2.1.0
"""

import os
import shutil
import zipfile
from pathlib import Path

VERSION = "2.1.0"

print("📦 Building Portable ZIP Distribution")
print("="*50)

# Check if EXE exists
if not Path("dist/GamaLauncher.exe").exists():
    print("❌ GamaLauncher.exe not found in dist/")
    print("   Run build_installer.py first to create the EXE")
    exit(1)

# Create portable folder
print("\n📁 Creating portable folder...")
portable_dir = Path("dist/GamaLauncher-Portable")

if portable_dir.exists():
    shutil.rmtree(portable_dir)

portable_dir.mkdir(parents=True)

# Copy EXE
print("   • Copying launcher...")
shutil.copy("dist/GamaLauncher.exe", portable_dir)

# Copy Logo
print("   • Copying logo...")
if Path("Logo.jpg").exists():
    shutil.copy("Logo.jpg", portable_dir)

# Copy ALL mods
print("   • Copying mods...")
if Path("mods").exists():
    shutil.copytree("mods", portable_dir / "mods")
    mod_count = sum(1 for _ in (portable_dir / "mods").rglob("*.jar"))
    print(f"     ✓ Copied {mod_count} mods")
else:
    print("     ⚠️  Warning: mods folder not found!")

# Copy ALL shaderpacks
print("   • Copying shaderpacks...")
if Path("shaderpacks").exists():
    shutil.copytree("shaderpacks", portable_dir / "shaderpacks")
    shader_count = sum(1 for _ in (portable_dir / "shaderpacks").rglob("*.zip"))
    print(f"     ✓ Copied {shader_count} shaderpacks")
else:
    print("     ⚠️  Warning: shaderpacks folder not found!")

# Copy config
print("   • Copying config...")
if Path("mod_lists.json").exists():
    shutil.copy("mod_lists.json", portable_dir)

print("   • Copying version info...")
if Path("version.json").exists():
    shutil.copy("version.json", portable_dir)

# Create README with new tier names
print("   • Creating README...")
readme_content = f"""
╔═══════════════════════════════════════════════════════════════╗
║          GAMA LAUNCHER v{VERSION} - PORTABLE EDITION           ║
╚═══════════════════════════════════════════════════════════════╝

📦 WHAT'S INCLUDED:

✓ Gama Launcher (GamaLauncher.exe)
✓ All mods (base, medium, heavy, ultimate folders)
✓ All shaderpacks (Complementary Reimagined & Unbound)
✓ Configuration files

🚀 HOW TO USE:

1. Extract this entire folder anywhere you want
2. Run GamaLauncher.exe
3. Select your quality preset
4. Enable shaders if desired (Medium and above)
5. Enter your username
6. Click "LAUNCH GAME"

📁 FILE LOCATIONS:

• This folder: Contains mods and shaders (read-only)
• AppData folder: Game files, Java, Minecraft
  (C:\\Users\\YourName\\AppData\\Roaming\\GamaLauncher)

💡 TIPS:

• First launch downloads Java + Minecraft (~250MB)
• First launch takes 2-4 minutes to load all mods
• You can move this folder anywhere - it's fully portable!
• Desktop stays clean - no files created there
• To uninstall: Delete this folder + AppData\\GamaLauncher

⚙️  SYSTEM REQUIREMENTS:

┌─────────────┬─────────┬──────────────────────────────────────┐
│ Preset      │ RAM     │ Hardware Requirements                │
├─────────────┼─────────┼──────────────────────────────────────┤
│ Very Low    │ 4GB     │ Any PC, integrated graphics          │
│ Low         │ 6GB     │ Any PC, integrated graphics          │
│ Medium      │ 8-10GB  │ GTX 960 / RX 560 (shaders optional)  │
│ High        │ 10-12GB │ GTX 1060 / RX 580 (shaders optional) │
│ Very High   │ 12-14GB │ GTX 1660 / RX 5600 XT + DH LODs      │
│ Ultra       │ 16-18GB │ RTX 3060 / RX 6700 XT (max visuals)  │
└─────────────┴─────────┴──────────────────────────────────────┘

Note: +2GB RAM recommended when shaders enabled

🎨 SHADER SUPPORT:

• Very Low / Low: Shaders NOT available (performance focus)
• Medium / High: Complementary Reimagined (optional)
• Very High: Complementary Reimagined (optional)
• Ultra: Complementary Unbound (optional)

Shaders are controlled by checkbox in launcher.

🔧 TROUBLESHOOTING:

• If launcher won't start: Install Visual C++ Redistributable
  https://aka.ms/vs/17/release/vc_redist.x64.exe

• If game crashes: Check logs in:
  AppData\\GamaLauncher\\runtime\\minecraft\\logs

• No sound in game: First launch may take time to download
  all assets. Wait for initial setup to complete.

• Server offline: Wait for admin to start server or play
  in singleplayer mode.

• Performance issues: Try lower preset or disable shaders.
  Very Low preset is optimized for 60+ FPS on weak systems.

═══════════════════════════════════════════════════════════════

📋 CHANGELOG v{VERSION}:

• NEW: Renamed tiers to standard game presets
  (Very Low/Low/Medium/High/Very High/Ultra)
• NEW: Shader checkbox - enable/disable per session
• FIXED: Vanilla sounds now load properly
• FIXED: Better asset downloading (no more silent blocks)
• IMPROVED: More accurate RAM requirements per tier
• IMPROVED: Better UI layout and tier descriptions

═══════════════════════════════════════════════════════════════

Made with ❤️  for Gama Server Community

═══════════════════════════════════════════════════════════════
"""

(portable_dir / "README.txt").write_text(readme_content, encoding='utf-8')

# Create ZIP archive
print("\n📦 Creating ZIP archive...")
zip_name = f"dist/GamaLauncher-Portable-v{VERSION}.zip"

with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
    total_files = sum(1 for _ in portable_dir.rglob('*') if _.is_file())
    current = 0
    
    for root, dirs, files in os.walk(portable_dir):
        for file in files:
            current += 1
            file_path = Path(root) / file
            arcname = file_path.relative_to(portable_dir.parent)
            zipf.write(file_path, arcname)
            
            if current % 10 == 0:
                print(f"   Packing: {current}/{total_files} files ({current*100//total_files}%)", end='\r')
    
    print(f"   Packing: {total_files}/{total_files} files (100%) ✓ ")

# Cleanup temp folder
print("   • Cleaning up temp folder...")
shutil.rmtree(portable_dir)

# Show results
print("\n" + "="*60)
print("✅ PORTABLE ZIP CREATED!")
print("="*60)

zip_size = Path(zip_name).stat().st_size / (1024*1024)

print(f"\n📦 File: {zip_name}")
print(f"📊 Size: {zip_size:.1f} MB")

print("\n📁 Contents:")
print(f"   • GamaLauncher.exe")
print(f"   • Logo.jpg")
print(f"   • mods/ (all tiers: base/medium/heavy/ultimate)")
print(f"   • shaderpacks/ (Complementary Reimagined & Unbound)")
print(f"   • mod_lists.json")
print(f"   • README.txt")

print("\n🎉 Ready to distribute!")
print("\n💡 Share this ZIP file:")
print("   • Upload to Google Drive / Mega / MediaFire")
print("   • Users extract and run GamaLauncher.exe")
print("   • Everything works out of the box!")
print("   • No installation required - fully portable!")

print("\n" + "="*60)
input("\nPress Enter to exit...")

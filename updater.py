"""
Auto-Updater for Gama Launcher
Checks GitHub releases and downloads updates
"""

import requests
import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Callable
import tempfile


class GamaUpdater:
    def __init__(self, current_version: str, github_repo: str, log_callback: Callable = None):
        """
        Args:
            current_version: Current version (e.g., "2.1.0")
            github_repo: GitHub repo in format "username/repo"
            log_callback: Function to call for logging
        """
        self.current_version = current_version
        self.github_repo = github_repo
        self.log_callback = log_callback or print
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
    
    def log(self, message: str):
        """Log message"""
        self.log_callback(message)
    
    def parse_version(self, version_str: str) -> tuple:
        """Parse version string to tuple for comparison"""
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')
        try:
            parts = version_str.split('.')
            return tuple(int(p) for p in parts[:3])  # Major.Minor.Patch
        except:
            return (0, 0, 0)
    
    def check_for_updates(self) -> Optional[Dict]:
        """
        Check GitHub for new version
        Returns: Dict with update info or None if no update
        """
        try:
            self.log("🔍 Checking for updates...")
            
            response = requests.get(self.api_url, timeout=10)
            
            if response.status_code == 404:
                self.log("⚠️  No releases found on GitHub")
                return None
            
            response.raise_for_status()
            release_data = response.json()
            
            latest_version = release_data.get("tag_name", "").lstrip('v')
            release_name = release_data.get("name", "")
            release_notes = release_data.get("body", "")
            
            current = self.parse_version(self.current_version)
            latest = self.parse_version(latest_version)
            
            if latest > current:
                self.log(f"🎉 New version available: v{latest_version}")
                
                # Find appropriate download asset
                assets = release_data.get("assets", [])
                download_url = None
                asset_name = None
                
                # Determine which asset to download based on platform
                if sys.platform == "win32":
                    # Look for Windows installer or portable
                    for asset in assets:
                        name = asset["name"].lower()
                        if "setup" in name or "installer" in name:
                            download_url = asset["browser_download_url"]
                            asset_name = asset["name"]
                            break
                        elif "portable" in name and name.endswith(".zip"):
                            download_url = asset["browser_download_url"]
                            asset_name = asset["name"]
                elif sys.platform == "darwin":
                    # macOS - look for DMG or app.zip
                    for asset in assets:
                        name = asset["name"].lower()
                        if name.endswith(".dmg") or (name.endswith(".zip") and "macos" in name):
                            download_url = asset["browser_download_url"]
                            asset_name = asset["name"]
                            break
                
                if not download_url:
                    self.log("⚠️  No compatible download found for your platform")
                    return None
                
                return {
                    "version": latest_version,
                    "name": release_name,
                    "notes": release_notes,
                    "download_url": download_url,
                    "asset_name": asset_name,
                    "assets": assets
                }
            else:
                self.log(f"✅ You have the latest version (v{self.current_version})")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"⚠️  Could not check for updates: {e}")
            return None
        except Exception as e:
            self.log(f"⚠️  Update check error: {e}")
            return None
    
    def download_update(self, download_url: str, asset_name: str, progress_callback: Callable = None) -> Optional[Path]:
        """
        Download update file
        Returns: Path to downloaded file or None
        """
        try:
            self.log(f"📥 Downloading {asset_name}...")
            
            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            # Save to temp directory
            temp_dir = Path(tempfile.gettempdir()) / "GamaLauncherUpdate"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            download_path = temp_dir / asset_name
            
            downloaded = 0
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0 and progress_callback:
                            progress = downloaded / total_size
                            progress_callback(progress)
                        
                        # Log every 5MB
                        if downloaded % (1024 * 1024 * 5) == 0:
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            self.log(f"   Downloaded: {mb_downloaded:.1f}MB / {mb_total:.1f}MB")
            
            self.log(f"✅ Download complete: {download_path}")
            return download_path
            
        except Exception as e:
            self.log(f"❌ Download failed: {e}")
            return None
    
    def apply_update_windows(self, installer_path: Path) -> bool:
        """
        Apply update on Windows
        Creates a batch script that replaces the EXE after launcher closes
        """
        try:
            if not getattr(sys, 'frozen', False):
                self.log("⚠️  Can't auto-update in development mode")
                self.log(f"📂 Installer downloaded to: {installer_path}")
                return False
            
            current_exe = Path(sys.executable)
            
            # Check if it's an installer (run it) or portable (replace EXE)
            if "setup" in installer_path.name.lower() or "installer" in installer_path.name.lower():
                # Run installer
                self.log("🚀 Launching installer...")
                self.log("   Please follow installation wizard")
                
                subprocess.Popen([str(installer_path)], shell=True)
                
                self.log("✅ Installer launched!")
                self.log("   Launcher will close now")
                return True
            
            elif installer_path.suffix.lower() == ".zip":
                # Portable update - extract and replace
                self.log("📦 Extracting portable update...")
                
                import zipfile
                extract_dir = installer_path.parent / "extracted"
                extract_dir.mkdir(exist_ok=True)
                
                with zipfile.ZipFile(installer_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Find the new EXE
                new_exe = None
                for item in extract_dir.rglob("GamaLauncher.exe"):
                    new_exe = item
                    break
                
                if not new_exe:
                    self.log("❌ Could not find GamaLauncher.exe in update")
                    return False
                
                # Create update batch script
                batch_script = installer_path.parent / "update.bat"
                
                batch_content = f"""@echo off
echo Updating Gama Launcher...
timeout /t 2 /nobreak >nul
taskkill /F /IM GamaLauncher.exe 2>nul
timeout /t 1 /nobreak >nul
copy /Y "{new_exe}" "{current_exe}"
if %errorlevel% equ 0 (
    echo Update successful!
    start "" "{current_exe}"
) else (
    echo Update failed!
    pause
)
del "%~f0"
"""
                
                with open(batch_script, 'w') as f:
                    f.write(batch_content)
                
                self.log("🚀 Applying update...")
                self.log("   Launcher will restart automatically")
                
                # Launch batch script and exit
                subprocess.Popen([str(batch_script)], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                return True
            
            else:
                self.log("⚠️  Unknown update file type")
                return False
                
        except Exception as e:
            self.log(f"❌ Update failed: {e}")
            return False
    
    def apply_update_macos(self, dmg_path: Path) -> bool:
        """Apply update on macOS"""
        try:
            self.log("🚀 Opening DMG installer...")
            subprocess.Popen(['open', str(dmg_path)])
            
            self.log("✅ Installer opened!")
            self.log("   Please drag app to Applications folder")
            self.log("   Launcher will close now")
            return True
            
        except Exception as e:
            self.log(f"❌ Update failed: {e}")
            return False
    
    def apply_update(self, download_path: Path) -> bool:
        """Apply update based on platform"""
        if sys.platform == "win32":
            return self.apply_update_windows(download_path)
        elif sys.platform == "darwin":
            return self.apply_update_macos(download_path)
        else:
            self.log("⚠️  Auto-update not supported on this platform")
            self.log(f"📂 Update downloaded to: {download_path}")
            return False

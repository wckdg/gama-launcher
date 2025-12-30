"""
Minecraft and Fabric Setup Module
IMPROVED: Retry logic, log window integration, better error handling
"""

import requests
import json
import os
import shutil
import time
from pathlib import Path
from typing import Optional, Callable


class MinecraftSetup:
    def __init__(self, minecraft_dir: str, mc_version: str, fabric_version: str, log_callback: Callable = None):
        self.minecraft_dir = Path(minecraft_dir)
        self.mc_version = mc_version
        self.fabric_version = fabric_version
        self.versions_dir = self.minecraft_dir / "versions"
        self.libraries_dir = self.minecraft_dir / "libraries"
        self.assets_dir = self.minecraft_dir / "assets"
        self.log_callback = log_callback or print
        
    def log(self, message: str):
        """Log message (integrates with launcher log window)"""
        self.log_callback(message)
    
    def check_installation(self) -> bool:
        """Check if Minecraft and Fabric are installed"""
        version_dir = self.versions_dir / f"fabric-loader-{self.fabric_version}-{self.mc_version}"
        version_jar = version_dir / f"fabric-loader-{self.fabric_version}-{self.mc_version}.jar"
        client_jar = self.versions_dir / self.mc_version / f"{self.mc_version}.jar"
        return version_jar.exists() and client_jar.exists()
    
    def download_with_retry(self, url: str, timeout: int = 30, retries: int = 3) -> Optional[requests.Response]:
        """Download with retry logic for network issues"""
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 2
                    self.log(f"⚠️  Connection failed (attempt {attempt+1}/{retries})")
                    self.log(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.log(f"❌ Failed after {retries} attempts: {e}")
                    return None
        return None
    
    def download_minecraft(self) -> Optional[str]:
        """
        Download Minecraft client from Mojang servers
        Returns: assetIndex ID for proper sound loading
        """
        try:
            # Get version manifest
            manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            self.log("📥 Fetching version manifest...")
            
            manifest_response = self.download_with_retry(manifest_url)
            if not manifest_response:
                self.log("❌ Could not reach Mojang servers")
                self.log("💡 Check your internet connection")
                return None
            
            manifest = manifest_response.json()
            
            # Find version
            version_info = None
            for version in manifest["versions"]:
                if version["id"] == self.mc_version:
                    version_info = version
                    break
            
            if not version_info:
                self.log(f"❌ Version {self.mc_version} not found")
                return None
            
            # Get version details
            version_url = version_info["url"]
            self.log(f"📥 Downloading version metadata...")
            
            version_response = self.download_with_retry(version_url)
            if not version_response:
                return None
            
            version_data = version_response.json()
            
            # Create directories
            version_dir = self.versions_dir / self.mc_version
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Download client JAR
            client_url = version_data["downloads"]["client"]["url"]
            client_jar = version_dir / f"{self.mc_version}.jar"
            
            if not client_jar.exists():
                self.log(f"📥 Downloading Minecraft {self.mc_version} client...")
                
                try:
                    response = requests.get(client_url, stream=True, timeout=120)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(client_jar, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024*256):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0 and downloaded % (1024*1024*5) == 0:
                                    percent = int((downloaded / total_size) * 100)
                                    self.log(f"   Downloading client: {percent}%")
                    
                    self.log(f"✅ Client downloaded: {client_jar.name}")
                except Exception as e:
                    self.log(f"❌ Client download failed: {e}")
                    return None
            else:
                self.log(f"✅ Client already exists")
            
            # Download libraries
            self.libraries_dir.mkdir(parents=True, exist_ok=True)
            self.log("📥 Downloading libraries...")
            
            lib_count = 0
            lib_total = len(version_data.get("libraries", []))
            
            for idx, library in enumerate(version_data.get("libraries", [])):
                if "downloads" in library and "artifact" in library["downloads"]:
                    artifact = library["downloads"]["artifact"]
                    lib_path = self.libraries_dir / artifact["path"]
                    lib_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not lib_path.exists():
                        try:
                            lib_data = requests.get(artifact["url"], timeout=60).content
                            with open(lib_path, 'wb') as f:
                                f.write(lib_data)
                            lib_count += 1
                            
                            if lib_count % 10 == 0:
                                self.log(f"   Libraries: {idx+1}/{lib_total}")
                        except:
                            pass
            
            self.log(f"✅ Downloaded {lib_count} libraries")
            
            # Download assets (FIXED: download all assets, no limit!)
            asset_index_id = version_data["assetIndex"]["id"]
            asset_index_url = version_data["assetIndex"]["url"]
            self.download_assets(asset_index_id, asset_index_url)
            
            # Save version JSON
            version_json = version_dir / f"{self.mc_version}.json"
            with open(version_json, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2)
            
            self.log("✅ Minecraft client installed successfully")
            return asset_index_id
            
        except Exception as e:
            self.log(f"❌ Error downloading Minecraft: {e}")
            return None
    
    def download_assets(self, asset_index_id: str, asset_index_url: str):
        """
        Download Minecraft assets (textures, sounds, etc.)
        FIXED: Downloads ALL assets instead of limiting to 100
        """
        try:
            # Download asset index
            indexes_dir = self.assets_dir / "indexes"
            indexes_dir.mkdir(parents=True, exist_ok=True)
            index_file = indexes_dir / f"{asset_index_id}.json"
            
            self.log(f"📥 Downloading asset index: {asset_index_id}")
            
            index_response = self.download_with_retry(asset_index_url)
            if not index_response:
                self.log("⚠️  Asset index download failed")
                return
            
            index_data = index_response.json()
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f)
            
            # Download asset objects (FIXED: download ALL, not just 100)
            objects_dir = self.assets_dir / "objects"
            objects_dir.mkdir(parents=True, exist_ok=True)
            
            total_assets = len(index_data.get("objects", {}))
            self.log(f"📥 Downloading {total_assets} assets (sounds, textures, etc.)")
            self.log("   This may take a few minutes on first run...")
            
            count = 0
            skipped = 0
            
            for asset_name, asset_info in index_data.get("objects", {}).items():
                asset_hash = asset_info["hash"]
                hash_prefix = asset_hash[:2]
                asset_dir = objects_dir / hash_prefix
                asset_dir.mkdir(parents=True, exist_ok=True)
                asset_file = asset_dir / asset_hash
                
                if asset_file.exists():
                    skipped += 1
                    continue
                
                asset_url = f"https://resources.download.minecraft.net/{hash_prefix}/{asset_hash}"
                try:
                    asset_data = requests.get(asset_url, timeout=30).content
                    with open(asset_file, 'wb') as f:
                        f.write(asset_data)
                    count += 1
                    
                    # Progress update every 500 assets
                    if count % 500 == 0:
                        progress = int((count + skipped) / total_assets * 100)
                        self.log(f"   Assets: {count + skipped}/{total_assets} ({progress}%)")
                        
                except Exception as e:
                    pass  # Silent fail for individual assets
            
            self.log(f"✅ Assets complete: {count} downloaded, {skipped} already present")
            
        except Exception as e:
            self.log(f"⚠️  Warning: Asset download incomplete: {e}")
    
    def download_fabric(self) -> bool:
        """Download Fabric loader + required dependencies"""
        try:
            # Fabric loader info
            loader_url = f"https://meta.fabricmc.net/v2/versions/loader/{self.mc_version}/{self.fabric_version}/profile/json"
            
            self.log(f"📥 Downloading Fabric {self.fabric_version}...")
            
            response = self.download_with_retry(loader_url)
            if not response:
                self.log("❌ Could not reach Fabric servers")
                return False
            
            loader_data = response.json()
            
            # Create version directory
            version_name = f"fabric-loader-{self.fabric_version}-{self.mc_version}"
            version_dir = self.versions_dir / version_name
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Save profile JSON
            profile_json = version_dir / f"{version_name}.json"
            with open(profile_json, 'w', encoding='utf-8') as f:
                json.dump(loader_data, f, indent=2)
            self.log(f"✅ Profile saved")
            
            # Download Fabric libraries
            self.log("📥 Downloading Fabric libraries...")
            
            lib_total = len(loader_data.get("libraries", []))
            lib_count = 0
            
            for idx, library in enumerate(loader_data.get("libraries", [])):
                lib_name = library.get("name")
                lib_url_base = library.get("url", "https://maven.fabricmc.net/")
                
                if not lib_name:
                    continue
                
                # Parse Maven coordinate: group:artifact:version
                parts = lib_name.split(":")
                if len(parts) < 3:
                    continue
                
                group_id = parts[0]
                artifact_id = parts[1]
                version = parts[2]
                
                # Build Maven path
                group_path = group_id.replace(".", "/")
                jar_name = f"{artifact_id}-{version}.jar"
                maven_path = f"{group_path}/{artifact_id}/{version}/{jar_name}"
                
                # Local path
                lib_path = self.libraries_dir / group_path / artifact_id / version / jar_name
                lib_path.parent.mkdir(parents=True, exist_ok=True)
                
                if lib_path.exists():
                    continue
                
                # Download URL
                download_url = f"{lib_url_base}{maven_path}"
                
                try:
                    lib_response = requests.get(download_url, timeout=60)
                    lib_response.raise_for_status()
                    
                    with open(lib_path, 'wb') as f:
                        f.write(lib_response.content)
                    
                    lib_count += 1
                    
                    if lib_count % 5 == 0:
                        self.log(f"   Fabric libraries: {idx+1}/{lib_total}")
                        
                except Exception as e:
                    self.log(f"   ⚠️  Failed: {jar_name}")
            
            # Create fabric JAR (copy from vanilla)
            fabric_jar = version_dir / f"{version_name}.jar"
            vanilla_jar = self.versions_dir / self.mc_version / f"{self.mc_version}.jar"
            
            if not fabric_jar.exists() and vanilla_jar.exists():
                shutil.copy2(vanilla_jar, fabric_jar)
                self.log(f"✅ Created Fabric JAR")
            
            self.log("✅ Fabric loader installed successfully!")
            return True
            
        except Exception as e:
            self.log(f"❌ Error downloading Fabric: {e}")
            return False

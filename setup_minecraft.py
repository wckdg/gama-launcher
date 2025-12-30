# -*- coding: utf-8 -*-
"""
Minecraft and Fabric Setup Module
Downloads official Minecraft client and Fabric loader
"""

import requests
import json
import os
from pathlib import Path
import shutil

class MinecraftSetup:
    def __init__(self, minecraft_dir: str, mc_version: str, fabric_version: str, log_callback=None):
        self.minecraft_dir = Path(minecraft_dir)
        self.mc_version = mc_version
        self.fabric_version = fabric_version
        self.versions_dir = self.minecraft_dir / "versions"
        self.libraries_dir = self.minecraft_dir / "libraries"
        self.assets_dir = self.minecraft_dir / "assets"
        self.log = log_callback if log_callback else print
    
    def check_installation(self) -> bool:
        """Check if Minecraft and Fabric are installed"""
        version_dir = self.versions_dir / f"fabric-loader-{self.fabric_version}-{self.mc_version}"
        version_json = version_dir / f"fabric-loader-{self.fabric_version}-{self.mc_version}.json"
        client_jar = self.versions_dir / self.mc_version / f"{self.mc_version}.jar"
        
        return version_json.exists() and client_jar.exists()
    
    def download_minecraft(self) -> str:
        """Download Minecraft client from Mojang servers - Returns assetIndex ID"""
        try:
            # Get version manifest
            manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            self.log(f"Fetching version manifest...")
            manifest = requests.get(manifest_url, timeout=30).json()
            
            # Find version
            version_info = None
            for version in manifest["versions"]:
                if version["id"] == self.mc_version:
                    version_info = version
                    break
            
            if not version_info:
                self.log(f"Version {self.mc_version} not found")
                return None
            
            # Get version details
            version_url = version_info["url"]
            self.log(f"Downloading version manifest...")
            version_data = requests.get(version_url, timeout=30).json()
            
            # Create directories
            version_dir = self.versions_dir / self.mc_version
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Download client JAR
            client_url = version_data["downloads"]["client"]["url"]
            client_jar = version_dir / f"{self.mc_version}.jar"
            
            self.log(f"Downloading Minecraft {self.mc_version} client...")
            response = requests.get(client_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(client_jar, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and downloaded % (1024*1024*5) == 0:  # Every 5MB
                        percent = (downloaded / total_size) * 100
                        self.log(f"  {percent:.0f}% ({downloaded/(1024*1024):.1f}MB)")
            
            self.log(f"✓ Client JAR downloaded")
            
            # Download libraries
            self.libraries_dir.mkdir(parents=True, exist_ok=True)
            self.log("Downloading vanilla libraries...")
            
            lib_count = 0
            for library in version_data.get("libraries", []):
                if "downloads" in library and "artifact" in library["downloads"]:
                    artifact = library["downloads"]["artifact"]
                    lib_path = self.libraries_dir / artifact["path"]
                    lib_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not lib_path.exists():
                        try:
                            lib_data = requests.get(artifact["url"], timeout=30).content
                            with open(lib_path, 'wb') as f:
                                f.write(lib_data)
                            lib_count += 1
                        except:
                            pass
            
            self.log(f"✓ Downloaded {lib_count} libraries")
            
            # Download assets
            asset_index_id = self.download_assets(version_data)
            
            # Save version JSON
            version_json = version_dir / f"{self.mc_version}.json"
            with open(version_json, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2)
            
            self.log("✓ Minecraft client ready")
            return asset_index_id
            
        except Exception as e:
            self.log(f"✗ Minecraft download error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_assets(self, version_data: dict) -> str:
        """Download Minecraft assets - Returns assetIndex ID"""
        try:
            asset_index = version_data["assetIndex"]
            asset_url = asset_index["url"]
            asset_index_id = asset_index["id"]
            
            # Download asset index
            indexes_dir = self.assets_dir / "indexes"
            indexes_dir.mkdir(parents=True, exist_ok=True)
            
            index_file = indexes_dir / f"{asset_index_id}.json"
            
            self.log(f"Downloading asset index ({asset_index_id})...")
            index_data = requests.get(asset_url, timeout=30).json()
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f)
            
            # Download ALL asset objects (for sounds to work)
            objects_dir = self.assets_dir / "objects"
            objects_dir.mkdir(parents=True, exist_ok=True)
            
            total_assets = len(index_data.get("objects", {}))
            self.log(f"Downloading {total_assets} assets (required for sounds)...")
            self.log("This may take a few minutes...")
            
            count = 0
            failed = 0
            
            for asset_name, asset_info in index_data.get("objects", {}).items():
                asset_hash = asset_info["hash"]
                hash_prefix = asset_hash[:2]
                
                asset_dir = objects_dir / hash_prefix
                asset_dir.mkdir(parents=True, exist_ok=True)
                
                asset_file = asset_dir / asset_hash
                
                if not asset_file.exists():
                    asset_url = f"https://resources.download.minecraft.net/{hash_prefix}/{asset_hash}"
                    try:
                        asset_data = requests.get(asset_url, timeout=10).content
                        with open(asset_file, 'wb') as f:
                            f.write(asset_data)
                        count += 1
                        
                        # Progress update every 100 assets
                        if count % 100 == 0:
                            percent = (count / total_assets) * 100
                            self.log(f"  {percent:.0f}% ({count}/{total_assets})")
                    except:
                        failed += 1
            
            self.log(f"✓ Assets downloaded: {count} new, {failed} failed")
            return asset_index_id
            
        except Exception as e:
            self.log(f"⚠️ Asset download incomplete: {e}")
            return asset_index.get("id", self.mc_version)
    
    def download_fabric(self) -> bool:
        """Download Fabric loader"""
        try:
            # Fabric loader info
            loader_url = f"https://meta.fabricmc.net/v2/versions/loader/{self.mc_version}/{self.fabric_version}/profile/json"
            
            self.log(f"Downloading Fabric {self.fabric_version}...")
            response = requests.get(loader_url, timeout=30)
            response.raise_for_status()
            
            loader_data = response.json()
            
            # Create version directory
            version_name = f"fabric-loader-{self.fabric_version}-{self.mc_version}"
            version_dir = self.versions_dir / version_name
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Save profile JSON
            profile_json = version_dir / f"{version_name}.json"
            with open(profile_json, 'w', encoding='utf-8') as f:
                json.dump(loader_data, f, indent=2)
            
            self.log(f"✓ Fabric profile saved")
            
            # Download Fabric libraries
            self.log("Downloading Fabric libraries...")
            
            lib_count = 0
            for library in loader_data.get("libraries", []):
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
                    lib_response = requests.get(download_url, timeout=30)
                    lib_response.raise_for_status()
                    
                    with open(lib_path, 'wb') as f:
                        f.write(lib_response.content)
                    
                    lib_count += 1
                except Exception as e:
                    self.log(f"  ⚠️ Failed: {jar_name}")
            
            self.log(f"✓ Downloaded {lib_count} Fabric libraries")
            
            # Create fabric JAR (copy from vanilla)
            fabric_jar = version_dir / f"{version_name}.jar"
            vanilla_jar = self.versions_dir / self.mc_version / f"{self.mc_version}.jar"
            
            if not fabric_jar.exists() and vanilla_jar.exists():
                shutil.copy2(vanilla_jar, fabric_jar)
                self.log(f"✓ Created Fabric JAR")
            
            self.log("✓ Fabric loader ready")
            return True
            
        except Exception as e:
            self.log(f"✗ Fabric download error: {e}")
            import traceback
            traceback.print_exc()
            return False

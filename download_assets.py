"""
Download all Minecraft assets once for distribution
Run this on your PC to pre-download assets
"""

import requests
import json
from pathlib import Path

MINECRAFT_VERSION = "1.20.1"

def download_assets():
    """Download all assets for distribution"""
    
    # Create assets directory structure
    assets_dir = Path("assets")
    objects_dir = assets_dir / "objects"
    indexes_dir = assets_dir / "indexes"
    
    objects_dir.mkdir(parents=True, exist_ok=True)
    indexes_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Downloading Minecraft {MINECRAFT_VERSION} assets...")
    print("="*50)
    
    # Get version manifest
    print("🔍 Fetching version manifest...")
    manifest_url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    manifest = requests.get(manifest_url, timeout=30).json()
    
    # Find version URL
    version_url = None
    for v in manifest["versions"]:
        if v["id"] == MINECRAFT_VERSION:
            version_url = v["url"]
            break
    
    if not version_url:
        print(f"❌ Version {MINECRAFT_VERSION} not found!")
        return False
    
    print(f"✓ Found version URL")
    
    # Get version data
    print("📥 Downloading version data...")
    version_data = requests.get(version_url, timeout=30).json()
    asset_index_url = version_data["assetIndex"]["url"]
    asset_index_id = version_data["assetIndex"]["id"]
    
    # Download asset index
    print(f"📥 Downloading asset index: {asset_index_id}")
    asset_index = requests.get(asset_index_url, timeout=30).json()
    
    # Save asset index
    index_file = indexes_dir / f"{asset_index_id}.json"
    with open(index_file, 'w') as f:
        json.dump(asset_index, f, indent=2)
    print(f"✓ Saved asset index to {index_file}")
    
    # Download all assets
    assets = asset_index.get("objects", {})
    total = len(assets)
    
    print(f"\n📦 Downloading {total} asset files...")
    print("This will take 10-15 minutes...\n")
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    session = requests.Session()
    
    for i, (asset_name, asset_data) in enumerate(assets.items(), 1):
        hash_code = asset_data["hash"]
        hash_prefix = hash_code[:2]
        
        object_file = objects_dir / hash_prefix / hash_code
        
        # Skip if already exists
        if object_file.exists():
            skipped += 1
            if i % 100 == 0:
                print(f"Progress: {i}/{total} ({skipped} already cached)")
            continue
        
        object_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Download
        asset_url = f"https://resources.download.minecraft.net/{hash_prefix}/{hash_code}"
        
        try:
            response = session.get(asset_url, timeout=15)
            response.raise_for_status()
            
            with open(object_file, 'wb') as f:
                f.write(response.content)
            
            downloaded += 1
            
            # Progress every 50 files
            if downloaded % 50 == 0:
                percent = (i / total) * 100
                print(f"Progress: {percent:.1f}% - {downloaded} downloaded, {skipped} cached")
        
        except Exception as e:
            failed += 1
            if failed <= 10:
                print(f"⚠️  Failed: {asset_name[:40]}... - {e}")
    
    session.close()
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in objects_dir.rglob('*') if f.is_file())
    total_size_mb = total_size / (1024 * 1024)
    
    print("\n" + "="*50)
    print("✅ DOWNLOAD COMPLETE!")
    print("="*50)
    print(f"Downloaded: {downloaded} files")
    print(f"Cached: {skipped} files")
    print(f"Failed: {failed} files")
    print(f"Total size: {total_size_mb:.1f} MB")
    print(f"\n📂 Assets saved to: {assets_dir.absolute()}")
    print("\nNow add this folder to your installer/portable builds!")
    print("="*50)
    
    return True

if __name__ == "__main__":
    download_assets()

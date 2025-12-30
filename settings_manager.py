"""
Minecraft Settings Manager - REWRITTEN
Automatically configures Minecraft + Mod settings based on quality tier
NEW: Supports Very Low/Low/Medium/High/Very High/Ultra
NEW: Shaders controlled by checkbox (not hardcoded per tier)
"""

from pathlib import Path
from typing import Dict
import json


class MinecraftSettingsManager:
    """Manages Minecraft options.txt, shader config, and mod configs"""
    
    def __init__(self, minecraft_dir: Path):
        self.minecraft_dir = minecraft_dir
        self.options_file = minecraft_dir / "options.txt"
        self.iris_config = minecraft_dir / "config" / "iris.properties"
        self.dh_config = minecraft_dir / "config" / "DistantHorizons.toml"
        self.settings_tracker = minecraft_dir / "launcher_settings.json"
        
        # Settings templates for each tier
        self.tier_settings = {
            "Very Low": {
                "renderDistance": 8,
                "simulationDistance": 6,
                "graphicsMode": 0,  # Fast
                "enableVsync": False,
                "maxFps": 0,  # Uncapped
                "fancyGraphics": False,
                "particles": 2,  # Minimal
                "fov": 70.0,
                "entityShadows": False,
                "bobView": False,
                "guiScale": 0,
                "mipmapLevels": 0,
                "biomeBlendRadius": 0,
                "ao": False,
                "clouds": False,
                "distant_horizons": False
            },
            "Low": {
                "renderDistance": 10,
                "simulationDistance": 8,
                "graphicsMode": 0,  # Fast
                "enableVsync": False,
                "maxFps": 0,
                "fancyGraphics": False,
                "particles": 1,  # Decreased
                "fov": 70.0,
                "entityShadows": False,
                "bobView": True,
                "guiScale": 0,
                "mipmapLevels": 1,
                "biomeBlendRadius": 1,
                "ao": False,
                "clouds": True,
                "distant_horizons": False
            },
            "Medium": {
                "renderDistance": 10,
                "simulationDistance": 8,
                "graphicsMode": 1,  # Fancy
                "enableVsync": False,
                "maxFps": 0,
                "fancyGraphics": True,
                "particles": 0,  # All
                "fov": 80.0,
                "entityShadows": True,
                "bobView": True,
                "guiScale": 0,
                "mipmapLevels": 2,
                "biomeBlendRadius": 2,
                "ao": True,
                "clouds": True,
                "distant_horizons": False
            },
            "High": {
                "renderDistance": 12,
                "simulationDistance": 8,
                "graphicsMode": 1,  # Fancy
                "enableVsync": False,
                "maxFps": 0,
                "fancyGraphics": True,
                "particles": 0,
                "fov": 85.0,
                "entityShadows": True,
                "bobView": True,
                "guiScale": 0,
                "mipmapLevels": 3,
                "biomeBlendRadius": 3,
                "ao": True,
                "clouds": True,
                "distant_horizons": False
            },
            "Very High": {
                "renderDistance": 12,
                "simulationDistance": 10,
                "graphicsMode": 1,  # Fancy
                "enableVsync": False,
                "maxFps": 0,
                "fancyGraphics": True,
                "particles": 0,
                "fov": 90.0,
                "entityShadows": True,
                "bobView": True,
                "guiScale": 0,
                "mipmapLevels": 4,
                "biomeBlendRadius": 5,
                "ao": True,
                "clouds": True,
                "distant_horizons": True,
                "dh_render_distance": 256,
                "dh_quality": "HIGH"
            },
            "Ultra": {
                "renderDistance": 14,
                "simulationDistance": 10,
                "graphicsMode": 2,  # Fabulous
                "enableVsync": False,
                "maxFps": 0,
                "fancyGraphics": True,
                "particles": 0,
                "fov": 90.0,
                "entityShadows": True,
                "bobView": True,
                "guiScale": 0,
                "mipmapLevels": 4,
                "biomeBlendRadius": 7,
                "ao": True,
                "clouds": True,
                "distant_horizons": True,
                "dh_render_distance": 512,
                "dh_quality": "EXTREME"
            }
        }
    
    def _load_settings_tracker(self) -> Dict:
        """Load tracker file that records last used tier and shader state"""
        if self.settings_tracker.exists():
            try:
                with open(self.settings_tracker, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"last_tier_used": None, "last_shaders_used": False}
    
    def _save_settings_tracker(self, tracker: Dict):
        """Save tracker file"""
        try:
            with open(self.settings_tracker, 'w', encoding='utf-8') as f:
                json.dump(tracker, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save settings tracker: {e}")
    
    def apply_settings(self, tier: str, shaders_enabled: bool, shaderpack: str = None, force: bool = False) -> bool:
        """
        Apply settings for the selected tier + shader state
        Returns True if settings were changed, False if using saved settings
        """
        if tier not in self.tier_settings:
            print(f"Warning: Unknown tier '{tier}'")
            return False
        
        # Load tracker
        tracker = self._load_settings_tracker()
        last_tier = tracker.get("last_tier_used", None)
        last_shaders = tracker.get("last_shaders_used", False)
        
        # Check if tier or shader state changed
        tier_changed = (last_tier != tier)
        shader_changed = (last_shaders != shaders_enabled)
        
        if not force and not tier_changed and not shader_changed:
            # Same tier and shader state - use saved settings
            print(f"✓ Using your saved {tier} settings (custom changes preserved)")
            
            # Still update shaders and DH in case config changed
            settings = self.tier_settings[tier]
            if shaders_enabled and shaderpack:
                self._enable_shaders(shaderpack)
            else:
                self._disable_shaders()
            
            if settings.get("distant_horizons"):
                self._configure_distant_horizons(settings)
            
            return False
        
        # Tier or shader changed - apply default settings
        if tier_changed:
            print(f"✓ Tier changed: {last_tier} → {tier}")
        if shader_changed:
            print(f"✓ Shaders changed: {last_shaders} → {shaders_enabled}")
        
        print(f"  Applying {tier} default settings...")
        
        settings = self.tier_settings[tier]
        
        # Apply Minecraft base settings
        self._write_options_txt(settings)
        
        # Apply shaders
        if shaders_enabled and shaderpack:
            self._enable_shaders(shaderpack)
        else:
            self._disable_shaders()
        
        # Apply Distant Horizons
        if settings.get("distant_horizons"):
            self._configure_distant_horizons(settings)
        
        # Update tracker with current tier and shader state
        tracker["last_tier_used"] = tier
        tracker["last_shaders_used"] = shaders_enabled
        self._save_settings_tracker(tracker)
        
        return True
    
    def _write_options_txt(self, settings: Dict):
        """Write or update options.txt file"""
        existing_options = {}
        
        if self.options_file.exists():
            try:
                with open(self.options_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            existing_options[key] = value
            except:
                pass
        
        # Update with tier settings
        existing_options['renderDistance'] = str(settings['renderDistance'])
        existing_options['simulationDistance'] = str(settings['simulationDistance'])
        existing_options['graphicsMode'] = str(settings['graphicsMode'])
        existing_options['enableVsync'] = 'true' if settings['enableVsync'] else 'false'
        existing_options['maxFps'] = str(settings['maxFps'])
        existing_options['fancyGraphics'] = 'true' if settings['fancyGraphics'] else 'false'
        existing_options['particles'] = str(settings['particles'])
        existing_options['fov'] = str(settings['fov'])
        existing_options['entityShadows'] = 'true' if settings['entityShadows'] else 'false'
        existing_options['bobView'] = 'true' if settings['bobView'] else 'false'
        existing_options['guiScale'] = str(settings['guiScale'])
        existing_options['mipmapLevels'] = str(settings['mipmapLevels'])
        existing_options['biomeBlendRadius'] = str(settings['biomeBlendRadius'])
        existing_options['ao'] = 'true' if settings.get('ao', True) else 'false'
        existing_options['renderClouds'] = 'true' if settings.get('clouds', True) else 'false'
        
        try:
            with open(self.options_file, 'w', encoding='utf-8') as f:
                for key, value in sorted(existing_options.items()):
                    f.write(f"{key}:{value}\n")
            
            graphics = ['Fast', 'Fancy', 'Fabulous'][settings['graphicsMode']]
            dh_info = ""
            if settings.get('distant_horizons'):
                dh_info = f" + DH:{settings.get('dh_render_distance', 0)}"
            
            print(f"  - Render: {settings['renderDistance']}{dh_info} | Graphics: {graphics} | FPS: Uncapped")
            
        except Exception as e:
            print(f"Warning: Could not write options.txt: {e}")
    
    def _enable_shaders(self, shaderpack: str):
        """Enable Iris shaders"""
        config_dir = self.minecraft_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.iris_config, 'w', encoding='utf-8') as f:
                f.write("enableShaders=true\n")
                f.write(f"shaderPack={shaderpack}\n")
                f.write("maxShadowRenderDistance=32\n")
            
            print(f"  - Shaders: ENABLED ({shaderpack})")
            
        except Exception as e:
            print(f"Warning: Could not configure shaders: {e}")
    
    def _disable_shaders(self):
        """Disable Iris shaders"""
        config_dir = self.minecraft_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.iris_config, 'w', encoding='utf-8') as f:
                f.write("enableShaders=false\n")
                f.write("shaderPack=\n")
            
            print(f"  - Shaders: DISABLED")
            
        except Exception as e:
            print(f"Warning: Could not configure shaders: {e}")
    
    def _configure_distant_horizons(self, settings: Dict):
        """Configure Distant Horizons mod settings"""
        config_dir = self.minecraft_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        if not settings.get('distant_horizons'):
            return
        
        dh_distance = settings.get('dh_render_distance', 256)
        dh_quality = settings.get('dh_quality', 'MEDIUM')
        
        # Quality presets
        quality_settings = {
            "MEDIUM": {
                "horizontalResolution": 1.0,
                "verticalQuality": "MEDIUM",
                "lodChunkRenderDistance": dh_distance,
                "drawMode": "FADING",
                "enableCaveMode": False
            },
            "HIGH": {
                "horizontalResolution": 1.25,
                "verticalQuality": "HIGH",
                "lodChunkRenderDistance": dh_distance,
                "drawMode": "FADING",
                "enableCaveMode": False
            },
            "EXTREME": {
                "horizontalResolution": 1.5,
                "verticalQuality": "EXTREME",
                "lodChunkRenderDistance": dh_distance,
                "drawMode": "FADING",
                "enableCaveMode": False
            }
        }
        
        quality = quality_settings.get(dh_quality, quality_settings["MEDIUM"])
        
        try:
            toml_content = f"""# Distant Horizons Config - Auto-configured by Gama Launcher

[client]

[client.advanced]

[client.advanced.lodBuilding]
# How far LOD chunks are rendered
lodChunkRenderDistance = {quality['lodChunkRenderDistance']}

[client.advanced.graphics]

[client.advanced.graphics.quality]
# Horizontal resolution multiplier (higher = sharper but slower)
horizontalResolution = {quality['horizontalResolution']}

# Vertical quality preset
verticalQuality = "{quality['verticalQuality']}"

# Draw mode (how LODs blend with regular chunks)
drawMode = "{quality['drawMode']}"

[client.advanced.graphics.advancedGraphics]
# Cave culling mode
enableCaveMode = {str(quality['enableCaveMode']).lower()}

# Disable fog to see distant LODs better
disableFog = true

# Enable LOD transparency for better visuals
enableTransparency = true

[client.advanced.worldGenerator]
# Distance for LOD generation
distanceGenerationMode = "BALANCED"
"""
            
            with open(self.dh_config, 'w', encoding='utf-8') as f:
                f.write(toml_content)
            
            print(f"  - Distant Horizons: {dh_distance} chunks, {dh_quality} quality")
            
        except Exception as e:
            print(f"Warning: Could not configure Distant Horizons: {e}")

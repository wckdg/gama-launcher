"""
Gama Server Launcher - VERSION 2.1.0
COMPLETE: New tiers + shader checkbox + sound fix + system recommendations + log window
"""

import customtkinter as ctk
import os
import sys
import json
import subprocess
import threading
import shutil
from pathlib import Path
from datetime import datetime
import requests
from typing import Dict, List, Optional
import re
from updater import GamaUpdater


# Configuration
APPNAME = "GAMA LAUNCHER"
VERSION = "2.1.0"
MCVERSION = "1.20.1"
FABRICVERSION = "0.17.2"
JAVAVERSION = "17"


class GamaLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
    
    # Detect paths based on platform and execution mode
        if getattr(sys, 'frozen', False):
        # Running as bundled executable
            if sys.platform == 'darwin':
            # macOS app bundle
                exe_path = Path(sys.executable)
                if 'Contents/MacOS' in str(exe_path):
                # Inside .app bundle - use Resources folder
                    self.base_dir = exe_path.parent.parent / 'Resources'
                else:
                # Standalone executable
                    self.base_dir = exe_path.parent
            else:
            # Windows EXE
                self.base_dir = Path(sys.executable).parent
        else:
        # Running as Python script
            self.base_dir = Path(__file__).parent
    
    # Safety check - ensure base_dir is valid
        if self.base_dir is None or not self.base_dir.exists():
            self.base_dir = Path.home() / 'GamaLauncher'
            self.base_dir.mkdir(parents=True, exist_ok=True)
            print(f"⚠️  Created fallback directory: {self.base_dir}")
    
        print(f"📁 Base directory: {self.base_dir}")
    
    # Set up directories
        self.mods_dir = self.base_dir / "mods"
        self.shaderpacks_dir = self.base_dir / "shaderpacks"
        self.mod_lists_file = self.base_dir / "mod_lists.json"
    
        # Runtime directory (where Minecraft/Java will be installed)
        if sys.platform == 'darwin':
            self.runtime_dir = Path.home() / 'Library' / 'Application Support' / 'GamaLauncher'
        else:
            self.runtime_dir = self.base_dir / "runtime"
    
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
    
        self.minecraft_dir = self.runtime_dir / ".minecraft"
        self.java_dir = self.runtime_dir / "java"
        self.fabric_dir = self.minecraft_dir / "versions"

    
    def log_print(self, message: str):
        """Print to console AND log window"""
        print(message)
        if hasattr(self, 'log_window'):
            try:
                self.log_window.configure(state="normal")
                self.log_window.insert("end", message + "\n")
                self.log_window.see("end")
                self.log_window.configure(state="disabled")
                self.update()
            except:
                pass
    
    def load_config(self):
        """Load saved configuration"""
        default_config = {
            "username": "",
            "last_tier": "High",
            "use_shaders": False,
            "ram_override": {}
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                
                # MIGRATION: Old tier names → New tier names
                tier_migration = {
                    "Super Light": "Very Low",
                    "Light": "Low",
                    "Medium": "Medium",
                    "Medium+Shaders": "Medium",
                    "Heavy": "Very High",
                    "Heavy+Shaders": "Very High",
                    "Ultimate": "Ultra"
                }
                
                old_tier = self.config.get("last_tier", "High")
                if old_tier in tier_migration:
                    self.config["last_tier"] = tier_migration[old_tier]
                    print(f"🔄 Migrated tier: {old_tier} → {self.config['last_tier']}")
                    self.save_config()
                
            except:
                self.config = default_config
        else:
            self.config = default_config
    
    def save_config(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.log_print(f"Error saving config: {e}")
    
    def load_mod_lists(self):
        """Load mod tier configurations"""
        mod_lists_file = self.mod_lists_file
        
        if not mod_lists_file.exists():
            # Create default with new tier names
            default_mod_lists = {
                "tiers": {
                    "Very Low": {
                        "mods": 83,
                        "ram": 4,
                        "mod_folders": ["base"],
                        "shader_policy": "DISALLOWED",
                        "shaderpack_when_enabled": None,
                        "description": "Maximum FPS for very weak systems. Fast graphics, minimal effects. No shaders available."
                    },
                    "Low": {
                        "mods": 83,
                        "ram": 6,
                        "mod_folders": ["base"],
                        "shader_policy": "DISALLOWED",
                        "shaderpack_when_enabled": None,
                        "description": "Good performance for integrated graphics. Balanced settings. No shaders available."
                    },
                    "Medium": {
                        "mods": 87,
                        "ram": 8,
                        "mod_folders": ["base", "medium"],
                        "shader_policy": "OPTIONAL",
                        "shaderpack_when_enabled": "ComplementaryReimagined_r5.6.1.zip",
                        "description": "Adds 3D skin layers, falling leaves, ambient sounds. Shaders optional (Complementary Reimagined)."
                    },
                    "High": {
                        "mods": 87,
                        "ram": 10,
                        "mod_folders": ["base", "medium"],
                        "shader_policy": "OPTIONAL",
                        "shaderpack_when_enabled": "ComplementaryReimagined_r5.6.1.zip",
                        "description": "Best balance of visuals and performance. Shaders optional (Complementary Reimagined)."
                    },
                    "Very High": {
                        "mods": 89,
                        "ram": 12,
                        "mod_folders": ["base", "medium", "heavy"],
                        "shader_policy": "OPTIONAL",
                        "shaderpack_when_enabled": "ComplementaryReimagined_r5.6.1.zip",
                        "description": "Adds Distant Horizons for 256+ chunk view distance. Shaders optional (Complementary Reimagined)."
                    },
                    "Ultra": {
                        "mods": 93,
                        "ram": 16,
                        "mod_folders": ["base", "medium", "heavy", "ultimate"],
                        "shader_policy": "OPTIONAL",
                        "shaderpack_when_enabled": "ComplementaryUnbound_r5.6.1.zip",
                        "description": "Maximum graphics: physics mod, sound physics, particles, blur effects. Shaders optional (Complementary Unbound)."
                    }
                }
            }
            
            with open(mod_lists_file, 'w', encoding='utf-8') as f:
                json.dump(default_mod_lists, f, indent=2)
            
            self.mod_lists = default_mod_lists
        else:
            with open(mod_lists_file, 'r', encoding='utf-8') as f:
                self.mod_lists = json.load(f)
    
    def detect_system_specs(self):
        """Detect system specs and recommend tier (with and without shaders)"""
        try:
            import psutil
            import platform
            
            # Get RAM
            ram_gb = round(psutil.virtual_memory().total / (1024**3))
            
            # Get CPU
            cpu_count = psutil.cpu_count(logical=False)
            cpu_name = "Unknown CPU"
            
            if os.name == "nt":
                try:
                    result = subprocess.run(['wmic', 'cpu', 'get', 'name'], 
                                           capture_output=True, text=True, timeout=3)
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        cpu_name = lines[1].strip()
                except:
                    pass
                
                if cpu_name == "Unknown CPU":
                    try:
                        import winreg
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                        cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                        winreg.CloseKey(key)
                    except:
                        pass
            
            if cpu_name == "Unknown CPU":
                cpu_name = platform.processor()
                if not cpu_name or len(cpu_name) < 3:
                    cpu_name = f"CPU ({cpu_count} cores)"
            
            # Get GPU
            gpu_name = "Unknown"
            gpu_vram = 0
            
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_name = gpu.name
                    gpu_vram = gpu.memoryTotal / 1024  # GB
                    
                    # Shorten GPU name
                    parts = gpu_name.split()
                    if "GeForce" in gpu_name or "RTX" in gpu_name or "GTX" in gpu_name or "RX" in gpu_name:
                        gpu_name = " ".join(parts[-3:]) if len(parts) >= 3 else gpu_name
            except:
                pass
            
            # Estimate GPU VRAM if not detected
            if gpu_vram == 0 and ram_gb >= 32:
                gpu_vram = 8  # Assume decent GPU
            
            # ===== RECOMMEND TIER WITHOUT SHADERS =====
            recommended_no_shaders = "Low"
            
            if ram_gb >= 16 and gpu_vram >= 8:
                recommended_no_shaders = "Ultra"
            elif ram_gb >= 12 and gpu_vram >= 6:
                recommended_no_shaders = "Very High"
            elif ram_gb >= 10 and gpu_vram >= 4:
                recommended_no_shaders = "High"
            elif ram_gb >= 8 and gpu_vram >= 2:
                recommended_no_shaders = "Medium"
            elif ram_gb >= 6:
                recommended_no_shaders = "Low"
            else:
                recommended_no_shaders = "Very Low"
            
            # ===== RECOMMEND TIER WITH SHADERS =====
            # Shaders need +2GB RAM and better GPU
            recommended_with_shaders = "Low"
            
            if ram_gb >= 18 and gpu_vram >= 10:
                recommended_with_shaders = "Ultra"
            elif ram_gb >= 14 and gpu_vram >= 8:
                recommended_with_shaders = "Very High"
            elif ram_gb >= 12 and gpu_vram >= 6:
                recommended_with_shaders = "High"
            elif ram_gb >= 10 and gpu_vram >= 4:
                recommended_with_shaders = "Medium"
            else:
                recommended_with_shaders = None  # Not recommended for shaders
            
            return {
                "ram_gb": ram_gb,
                "cpu_count": cpu_count,
                "cpu_name": cpu_name,
                "gpu_name": gpu_name,
                "gpu_vram_gb": round(gpu_vram, 1),
                "recommended_no_shaders": recommended_no_shaders,
                "recommended_with_shaders": recommended_with_shaders
            }
            
        except Exception as e:
            self.log_print(f"Could not detect system specs: {e}")
            return {
                "ram_gb": 8,
                "cpu_count": 4,
                "cpu_name": "Unknown",
                "gpu_name": "Unknown",
                "gpu_vram_gb": 0,
                "recommended_no_shaders": "Medium",
                "recommended_with_shaders": None
            }
    
    def setup_window(self):
        """Configure main window - LANDSCAPE DESIGN"""
        self.title(f"{APPNAME} v{VERSION}")
        self.geometry("1000x720")
        self.resizable(False, False)
        
        # Dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.configure(fg_color="#0a0a0a")
    
    def create_widgets(self):
        """Create all UI elements - NEW LAYOUT WITH LOG WINDOW"""
        
        # ========== HEADER ==========
        header_frame = ctk.CTkFrame(self, fg_color="#1a0000", corner_radius=0, height=100)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        content_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        content_frame.pack(expand=True)
        
        # Try to load logo
        try:
            from PIL import Image
            logo_path = self.base_dir / "Logo.jpg"
            if logo_path.exists():
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((60, 60), Image.Resampling.LANCZOS)
                logo_ctk = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(60, 60))
                logo_label = ctk.CTkLabel(content_frame, image=logo_ctk, text="")
                logo_label.pack(side="left", padx=(0, 15))
        except:
            pass
        
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="GAMA LAUNCHER",
            font=("Roboto", 36, "bold"),
            text_color="#ff0000"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text=f"Minecraft {MCVERSION} • Fabric {FABRICVERSION} • v{VERSION}",
            font=("Roboto", 14),
            text_color="#888888"
        ).pack(anchor="w")
        
        # ========== MAIN CONTENT (TWO COLUMNS) ==========
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        left_column = ctk.CTkFrame(main_frame, fg_color="transparent", width=440)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        left_column.pack_propagate(False)
        
        right_column = ctk.CTkFrame(main_frame, fg_color="transparent", width=440)
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        right_column.pack_propagate(False)
        
        # ========== LEFT: SYSTEM INFO ==========
        specs_frame = ctk.CTkFrame(left_column, fg_color="#1a0000", corner_radius=8)
        specs_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            specs_frame,
            text="💻 YOUR SYSTEM",
            font=("Roboto", 14, "bold"),
            text_color="#ff0000"
        ).pack(pady=(8, 2))
        
        specs_text = f"{self.detected_specs['cpu_name']}"
        if len(specs_text) > 50:
            specs_text = specs_text[:47] + "..."
        
        ctk.CTkLabel(
            specs_frame,
            text=specs_text,
            font=("Roboto", 11),
            text_color="#aaaaaa"
        ).pack()
        
        specs_text2 = f"{self.detected_specs['ram_gb']}GB RAM"
        if self.detected_specs['gpu_vram_gb'] > 0:
            specs_text2 += f" • {self.detected_specs['gpu_name']} ({self.detected_specs['gpu_vram_gb']}GB)"
        
        if len(specs_text2) > 60:
            gpu_short = self.detected_specs['gpu_name'].split()[0]
            specs_text2 = f"{self.detected_specs['ram_gb']}GB RAM • {gpu_short} ({self.detected_specs['gpu_vram_gb']}GB)"
        
        ctk.CTkLabel(
            specs_frame,
            text=specs_text2,
            font=("Roboto", 11),
            text_color="#aaaaaa"
        ).pack()
        
        # Recommendation WITHOUT shaders
        ctk.CTkLabel(
            specs_frame,
            text=f"⚡ Recommended: {self.detected_specs['recommended_no_shaders']}",
            font=("Roboto", 13, "bold"),
            text_color="#00ff00"
        ).pack(pady=(4, 0))
        
        # Recommendation WITH shaders
        if self.detected_specs['recommended_with_shaders']:
            ctk.CTkLabel(
                specs_frame,
                text=f"✨ With Shaders: {self.detected_specs['recommended_with_shaders']}",
                font=("Roboto", 13, "bold"),
                text_color="#00ddff"
            ).pack(pady=(2, 8))
        else:
            ctk.CTkLabel(
                specs_frame,
                text="✨ Shaders: Not Recommended",
                font=("Roboto", 12),
                text_color="#ff8800"
            ).pack(pady=(2, 8))
        
        # ========== LEFT: USERNAME ==========
        ctk.CTkLabel(
            left_column,
            text="⚡ USERNAME",
            font=("Roboto", 16, "bold"),
            text_color="#ff0000"
        ).pack(anchor="w", pady=(0, 4))
        
        self.username_entry = ctk.CTkEntry(
            left_column,
            placeholder_text="Enter your Minecraft username",
            height=50,
            font=("Roboto", 15),
            fg_color="#1a0000",
            border_color="#ff0000",
            border_width=2,
            text_color="#ffffff"
        )
        self.username_entry.pack(fill="x")
        
        if self.config["username"]:
            self.username_entry.insert(0, self.config["username"])
        
        self.username_error = ctk.CTkLabel(
            left_column,
            text="",
            font=("Roboto", 9),
            text_color="#ff4444"
        )
        self.username_error.pack(anchor="w", pady=(2, 10))
        
        # ========== LEFT: PROGRESS BAR ==========
        self.progress_bar = ctk.CTkProgressBar(
            left_column,
            height=18,
            corner_radius=9,
            fg_color="#1a0000",
            progress_color="#ff0000"
        )
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            left_column,
            text="Ready to launch",
            font=("Roboto", 12),
            text_color="#888888"
        )
        self.progress_label.pack(pady=(0, 10))
        
        # ========== LEFT: LAUNCH BUTTON ==========
        self.launch_btn = ctk.CTkButton(
            left_column,
            text="🚀 LAUNCH GAME",
            font=("Roboto", 26, "bold"),
            height=65,
            corner_radius=10,
            fg_color="#ff0000",
            hover_color="#cc0000",
            text_color="#ffffff",
            command=self.launch_game
        )
        self.launch_btn.pack(fill="x", pady=(0, 10))
        
        # ========== LEFT: LOG WINDOW ==========
        log_frame = ctk.CTkFrame(left_column, fg_color="#1a0000", corner_radius=8)
        log_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            log_frame,
            text="📋 LOG",
            font=("Roboto", 12, "bold"),
            text_color="#ff0000"
        ).pack(anchor="w", padx=8, pady=(6, 2))
        
        self.log_window = ctk.CTkTextbox(
            log_frame,
            height=120,
            font=("Consolas", 13),
            fg_color="#0a0a0a",
            text_color="#00ff00",
            wrap="word"
        )
        self.log_window.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log_window.configure(state="disabled")
        
        # Initial log message
        self.log_print("=== GAMA LAUNCHER v2.1.0 ===")
        self.log_print("Ready to launch!")
        
        # ========== RIGHT: QUALITY PRESETS ==========
        ctk.CTkLabel(
            right_column,
            text="🎮 QUALITY PRESET",
            font=("Roboto", 16, "bold"),
            text_color="#ff0000"
        ).pack(anchor="w", pady=(0, 8))
        
        # Use recommended tier (without shaders) if first launch
        default_tier = self.config.get("last_tier", self.detected_specs.get("recommended_no_shaders", "High"))
        self.tier_var = ctk.StringVar(value=default_tier)
        
        tier_scroll = ctk.CTkScrollableFrame(
            right_column,
            fg_color="transparent",
            height=280
        )
        tier_scroll.pack(fill="both", expand=False)
        
        tiers = self.mod_lists["tiers"]
        
        tier_icons = {
            "Very Low": "⚡",
            "Low": "🌙",
            "Medium": "⭐",
            "High": "💎",
            "Very High": "🔥",
            "Ultra": "👑"
        }
        
        for tier_name, tier_data in tiers.items():
            icon = tier_icons.get(tier_name, "")
            tier_btn = ctk.CTkRadioButton(
                tier_scroll,
                text=f"{icon} {tier_name} ({tier_data['mods']} mods, {tier_data['ram']}GB RAM)",
                variable=self.tier_var,
                value=tier_name,
                font=("Roboto", 14),
                command=self.update_tier_description,
                fg_color="#ff0000",
                hover_color="#cc0000",
                text_color="#ffffff"
            )
            tier_btn.pack(anchor="w", pady=3)
        
        # ========== RIGHT: DESCRIPTION ==========
        desc_frame = ctk.CTkFrame(right_column, fg_color="#1a0000", border_color="#ff0000", border_width=1)
        desc_frame.pack(fill="x", pady=(8, 0))
        
        self.tier_description = ctk.CTkTextbox(
            desc_frame,
            height=90,
            font=("Roboto", 13),
            wrap="word",
            fg_color="#1a0000",
            text_color="#cccccc"
        )
        self.tier_description.pack(fill="x", padx=8, pady=8)
        
        # ========== RIGHT: SHADER CHECKBOX + RAM INFO ==========
        shader_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        shader_frame.pack(fill="x", pady=(10, 0))
        
        self.shaders_var = ctk.BooleanVar(value=self.config.get("use_shaders", False))
        self.shaders_checkbox = ctk.CTkCheckBox(
            shader_frame,
            text="Enable Shaders (Iris)",
            variable=self.shaders_var,
            font=("Roboto", 14),
            fg_color="#ff0000",
            hover_color="#cc0000",
            text_color="#ffffff",
            command=self.on_shader_toggle
        )
        self.shaders_checkbox.pack(side="left")
        
        self.ram_display = ctk.CTkLabel(
            shader_frame,
            text="",
            font=("Roboto", 13),
            text_color="#00ff00"
        )
        self.ram_display.pack(side="right")
        
        # Update UI state
        self.update_tier_description()
        
        # ========== FOOTER ==========
        footer = ctk.CTkFrame(self, fg_color="#1a0000", corner_radius=0, height=35)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            footer,
            text="Ready to launch",
            font=("Roboto", 12),
            text_color="#888888"
        )
        self.status_label.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            footer,
            text=f"Modded Server • Voice Chat • Smart Mod Management",
            font=("Roboto", 11),
            text_color="#555555"
        ).pack(side="right", padx=20)
    
    def update_tier_description(self):
        """Update tier description text and shader checkbox state"""
        tier = self.tier_var.get()
        tier_data = self.mod_lists["tiers"][tier]
        
        # Update description
        self.tier_description.configure(state="normal")
        self.tier_description.delete("1.0", "end")
        self.tier_description.insert("1.0", tier_data["description"])
        self.tier_description.configure(state="disabled")
        
        # Update shader checkbox state (tier-gated)
        shader_policy = tier_data.get("shader_policy", "DISALLOWED")
        
        if shader_policy == "DISALLOWED":
            self.shaders_checkbox.configure(state="disabled")
            self.shaders_var.set(False)
            self.shaders_checkbox.configure(text="Enable Shaders (Not available for this tier)")
        else:
            self.shaders_checkbox.configure(state="normal")
            self.shaders_checkbox.configure(text="Enable Shaders (Iris)")
        
        # Update RAM display
        self.update_ram_display()
    
    def on_shader_toggle(self):
        """Handle shader checkbox toggle"""
        self.update_ram_display()
    
    def update_ram_display(self):
        """Update RAM requirement display"""
        tier = self.tier_var.get()
        tier_data = self.mod_lists["tiers"][tier]
        base_ram = tier_data["ram"]
        
        # Add +2GB if shaders enabled (realistic overhead)
        shaders_enabled = self.shaders_var.get()
        if shaders_enabled and tier_data.get("shader_policy") == "OPTIONAL":
            total_ram = base_ram + 2
            self.ram_display.configure(text=f"💾 {total_ram}GB RAM ({base_ram}+2 shaders)")
        else:
            self.ram_display.configure(text=f"💾 {base_ram}GB RAM")
    
    def update_status(self, text: str, color: str = "#cccccc"):
        """Update status label"""
        self.status_label.configure(text=text, text_color=color)
        self.update()
    
    def update_progress(self, value: float, text: str = ""):
        """Update progress bar (0.0 to 1.0)"""
        self.progress_bar.set(value)
        if text:
            self.progress_label.configure(text=text)
        self.update()
    
    def validate_username(self, username: str) -> bool:
        """Validate Minecraft username"""
        if len(username) < 3 or len(username) > 16:
            self.username_error.configure(text="Username must be 3-16 characters")
            return False
        
        if not re.match(r'^[A-Za-z0-9_]+$', username):
            self.username_error.configure(text="Only letters, numbers, and _ allowed")
            return False
        
        self.username_error.configure(text="")
        return True
    
    def check_server_status(self):
        """Check if Gama server is online"""
        try:
            import socket
            host = "supernova.dathost.net"
            port = 17225
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return {"online": True, "players": "?", "max": "20"}
            else:
                return {"online": False}
                
        except Exception as e:
            return {"online": False}
    def check_for_updates(self):
        """Check for updates on GitHub"""
        try:
        # GitHub repo 
            GITHUB_REPO = "wckdg/gama-launcher"  
        
            updater = GamaUpdater(VERSION, GITHUB_REPO, log_callback=self.log_print)
        
            update_info = updater.check_for_updates()
        
            if update_info:
                # Show update dialog
                self.show_update_dialog(update_info, updater)
        
        except Exception as e:
            self.log_print(f"Update check error: {e}")

    def show_update_dialog(self, update_info: Dict, updater: GamaUpdater):
        """Show update available dialog"""
        import tkinter.messagebox as msgbox
    
        message = f"""New version available: v{update_info['version']}

    Current version: v{VERSION}

    {update_info['name']}

    Release Notes:
    {update_info['notes'][:200]}...

    Would you like to download and install this update?"""
    
        result = msgbox.askyesno(
            "Update Available",
            message,
            icon='info'
        )
    
        if result:
            self.download_and_apply_update(update_info, updater)

    def download_and_apply_update(self, update_info: Dict, updater: GamaUpdater):
        """Download and apply update"""
        self.log_print("=" * 40)
        self.log_print("UPDATING LAUNCHER")
        self.log_print("=" * 40)
    
        self.launch_btn.configure(state="disabled", text="UPDATING...")
    
        def update_progress(progress: float):
            self.update_progress(progress, f"Downloading update: {int(progress*100)}%")
    
    # Download
        download_path = updater.download_update(
            update_info['download_url'],
            update_info['asset_name'],
            progress_callback=update_progress
        )
    
        if download_path:
        # Apply update
            success = updater.apply_update(download_path)
        
            if success:
                self.log_print("✅ Update will be applied on restart")
                # Close launcher
                self.after(2000, self.quit)
            else:
                self.log_print("⚠️  Manual installation required")
                self.launch_btn.configure(state="normal", text="🚀 LAUNCH GAME")
        else:
            self.log_print("❌ Update download failed")
            self.launch_btn.configure(state="normal", text="🚀 LAUNCH GAME")

    def check_java(self):
        """Check for Java 17 installation"""
        self.update_status("Checking Java installation...", "#ff8800")
        self.update_progress(0.1, "Checking Java...")
        self.log_print("Checking for Java 17...")
        
        java_exe = self.java_dir / "bin" / ("java.exe" if os.name == "nt" else "java")
        
        if not java_exe.exists():
            self.update_status("Downloading Java 17...", "#ffaa00")
            self.update_progress(0.2, "Downloading Java...")
            self.log_print("Java not found, downloading...")
            
            if self.download_java():
                self.update_status("Java 17 ready", "#00ff00")
                self.update_progress(1.0, "Java ready")
                self.log_print("✓ Java 17 ready!")
            else:
                self.update_status("Failed to download Java", "#ff0000")
                self.update_progress(0, "Java download failed")
                self.log_print("✗ Java download failed!")
                return
        else:
            self.update_status("Java 17 ready", "#00ff00")
            self.update_progress(1.0, "Java ready")
            self.log_print("✓ Java 17 found!")
    
    def download_java(self) -> bool:
        """Download portable Java 17 JRE"""
        try:
            if os.name == "nt":
                if sys.maxsize > 2**32:
                    platform = "windows"
                    arch = "x64"
                else:
                    platform = "windows"
                    arch = "x86"
            else:
                platform = "linux"
                arch = "x64"
            
            api_url = f"https://api.adoptium.net/v3/binary/latest/17/ga/{platform}/{arch}/jre/hotspot/normal/eclipse"
            
            self.java_dir.mkdir(parents=True, exist_ok=True)
            
            self.log_print(f"Downloading Java from Adoptium...")
            response = requests.get(api_url, stream=True, timeout=30)
            response.raise_for_status()
            
            if platform == "windows":
                zip_path = self.java_dir / "java.zip"
            else:
                zip_path = self.java_dir / "java.tar.gz"
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = downloaded / total_size
                        self.update_progress(0.2 + (percent * 0.3), f"Downloading Java: {int(percent*100)}%")
                        if downloaded % (1024*1024*10) == 0:  # Every 10MB
                            self.log_print(f"Downloaded: {downloaded/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB")
            
            self.update_progress(0.5, "Extracting Java...")
            self.update_status("Extracting Java...", "#ffaa00")
            self.log_print("Extracting Java...")
            
            if platform == "windows":
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.java_dir)
            else:
                import tarfile
                with tarfile.open(zip_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(self.java_dir)
            
            # Move contents up one level
            for item in self.java_dir.iterdir():
                if item.is_dir() and (item.name.startswith("jdk") or item.name.startswith("jre")):
                    for subitem in item.iterdir():
                        dest = self.java_dir / subitem.name
                        if dest.exists():
                            if dest.is_dir():
                                shutil.rmtree(dest)
                            else:
                                dest.unlink()
                        shutil.move(str(subitem), str(self.java_dir))
                    item.rmdir()
                    break
            
            zip_path.unlink()
            self.log_print("✓ Java extracted successfully!")
            
            return True
            
        except Exception as e:
            self.log_print(f"✗ Java download error: {e}")
            return False
    
    def setup_minecraft(self):
        """Setup Minecraft installation"""
        from setup_minecraft import MinecraftSetup
    
        self.update_status("Setting up Minecraft...", "#ff8800")
        self.update_progress(0.3, "Setting up Minecraft...")
        self.log_print("Setting up Minecraft...")
    
        # Pass log_print callback for integration
        setup = MinecraftSetup(
            str(self.minecraft_dir), 
            MCVERSION, 
            FABRICVERSION,
            log_callback=self.log_print  # NEW: Pass log function
        )
    
        if not setup.check_installation():
            self.update_status("Downloading Minecraft...", "#ffaa00")
            self.update_progress(0.4, "Downloading Minecraft...")
            self.log_print("Downloading Minecraft client...")
        
        # FIXED: Store assetIndex ID for sound loading
            self.asset_index_id = setup.download_minecraft()
        
            if not self.asset_index_id:
                self.update_status("Failed to download Minecraft", "#ff0000")
                self.log_print("✗ Minecraft download failed!")
                self.log_print("💡 Troubleshooting:")
                self.log_print("  1. Check your internet connection")
                self.log_print("  2. Disable VPN/proxy temporarily")
                self.log_print("  3. Check firewall/antivirus")
                self.log_print("  4. Try again in a few minutes")
                return False
        
            self.update_status("Downloading Fabric...", "#ffaa00")
            self.update_progress(0.5, "Downloading Fabric...")
            self.log_print("Downloading Fabric loader...")
        
            if not setup.download_fabric():
                self.update_status("Failed to download Fabric", "#ff0000")
                self.log_print("✗ Fabric download failed!")
                return False
        else:
        # Load assetIndex from existing installation
            version_json = self.minecraft_dir / "versions" / MCVERSION / f"{MCVERSION}.json"
            if version_json.exists():
                try:
                    with open(version_json, 'r', encoding='utf-8') as f:
                        version_data = json.load(f)
                        self.asset_index_id = version_data["assetIndex"]["id"]
                    self.log_print(f"✓ Using assetIndex: {self.asset_index_id}")
                except:
                    self.asset_index_id = MCVERSION  # Fallback
            else:
                self.asset_index_id = MCVERSION  # Fallback
        
        self.log_print("Configuring server list...")
        server_list = MinecraftServerList(self.minecraft_dir)
        server_list.add_gama_server()

        return True

    
    def prepare_mods(self):
        """Prepare mods for selected tier"""
        self.update_status("Preparing mods and shaders...", "#ff8800")
        self.update_progress(0.6, "Preparing mods and shaders...")
        self.log_print("Preparing mods...")
        
        tier = self.tier_var.get()
        tier_config = self.mod_lists["tiers"][tier]
        
        mods_dir = self.minecraft_dir / "mods"
        mods_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear existing mods
        for mod_file in mods_dir.glob("*.jar"):
            try:
                mod_file.unlink()
            except:
                pass
        
        # Copy required mods
        mod_categories = tier_config["mod_folders"]
        copied_count = 0
        
        for category in mod_categories:
            source_folder = self.mods_source_dir / category
            if source_folder.exists():
                for mod_file in source_folder.glob("*.jar"):
                    try:
                        shutil.copy2(mod_file, mods_dir)
                        copied_count += 1
                    except Exception as e:
                        self.log_print(f"Warning: Could not copy {mod_file.name}")
        
        self.log_print(f"✓ Copied {copied_count} mods")
        
        # Handle shaderpack
        shaders_enabled = self.shaders_var.get()
        shaderpack_name = tier_config.get("shaderpack_when_enabled")
        
        if shaders_enabled and shaderpack_name and tier_config.get("shader_policy") == "OPTIONAL":
            shaderpacks_dest = self.minecraft_dir / "shaderpacks"
            shaderpacks_dest.mkdir(parents=True, exist_ok=True)
            
            source_file = self.shaderpacks_dir / shaderpack_name
            dest_file = shaderpacks_dest / shaderpack_name
            
            if source_file.exists():
                try:
                    shutil.copy2(source_file, dest_file)
                    self.log_print(f"✓ Shaderpack: {shaderpack_name}")
                except Exception as e:
                    self.log_print(f"Warning: Could not copy shaderpack")
        else:
            # Clear shaderpacks folder if shaders disabled
            shaderpacks_dest = self.minecraft_dir / "shaderpacks"
            if shaderpacks_dest.exists():
                for old_shader in shaderpacks_dest.glob("*.zip"):
                    try:
                        old_shader.unlink()
                    except:
                        pass
        
        return True
    
    def launch_game(self):
        """Main launch function"""
        username = self.username_entry.get().strip()
        
        if not self.validate_username(username):
            return
        
        # Save config
        self.config["username"] = username
        self.config["last_tier"] = self.tier_var.get()
        self.config["use_shaders"] = self.shaders_var.get()
        self.save_config()
        
        self.launch_btn.configure(state="disabled", text="LAUNCHING...")
        self.update_progress(0, "Starting launch sequence...")
        self.log_print("\n=== LAUNCH SEQUENCE ===")
        
        threading.Thread(
            target=self.launch_sequence,
            args=(username,),
            daemon=True
        ).start()
    
    def launch_sequence(self, username: str):
        """Launch sequence thread"""
        try:
            # Setup Minecraft
            if not self.setup_minecraft():
                self.launch_btn.configure(state="normal", text="🚀 LAUNCH GAME")
                return
            
            # Prepare mods
            if not self.prepare_mods():
                self.launch_btn.configure(state="normal", text="🚀 LAUNCH GAME")
                return
            
            tier = self.tier_var.get()
            tier_config = self.mod_lists["tiers"][tier]
            
            base_ram = tier_config["ram"]
            shaders_enabled = self.shaders_var.get()
            
            # Add +2GB if shaders enabled
            ram = base_ram + 2 if (shaders_enabled and tier_config.get("shader_policy") == "OPTIONAL") else base_ram
            
            mod_count = tier_config["mods"]
            
            # Configure settings
            self.update_status("Configuring settings...", "#ff8800")
            self.update_progress(0.65, "Configuring settings...")
            self.log_print("Configuring game settings...")
            
            from settings_manager import MinecraftSettingsManager
            settings_manager = MinecraftSettingsManager(self.minecraft_dir)
            
            shaderpack = tier_config.get("shaderpack_when_enabled") if shaders_enabled else None
            
            was_applied = settings_manager.apply_settings(
                tier,
                shaders_enabled,
                shaderpack
            )
            
            if was_applied:
                self.log_print(f"✓ Applied {tier} settings")
            else:
                self.log_print(f"✓ Using saved {tier} settings")
            
            # Estimate startup time
            if mod_count == 83:
                estimated_time = "1-2 minutes"
            elif mod_count <= 89:
                estimated_time = "2-3 minutes"
            else:
                estimated_time = "3-4 minutes"
            
            self.log_print(f"Expected startup: {estimated_time}")
            self.log_print(f"Loading {mod_count} mods...")
            
            # Build launch configuration
            self.update_status("Building launch configuration...", "#ff8800")
            self.update_progress(0.7, "Building configuration...")
            self.log_print("Building launch configuration...")
            
            java_exe = self.java_dir / "bin" / ("java.exe" if os.name == "nt" else "java")
            version_name = f"fabric-loader-{FABRICVERSION}-{MCVERSION}"
            
            version_json_path = self.minecraft_dir / "versions" / version_name / f"{version_name}.json"
            
            if not version_json_path.exists():
                raise Exception(f"Fabric profile not found!")
            
            with open(version_json_path, 'r', encoding='utf-8') as f:
                fabric_profile = json.load(f)
            
            main_class = fabric_profile.get("mainClass")
            if not main_class:
                raise Exception("Main class not found!")
            
            # Build classpath
            classpath_parts = []
            libraries_dir = self.minecraft_dir / "libraries"
            
            self.log_print("Building classpath...")
            
            # Vanilla libraries
            vanilla_version_json = self.minecraft_dir / "versions" / MCVERSION / f"{MCVERSION}.json"
            if vanilla_version_json.exists():
                with open(vanilla_version_json, 'r', encoding='utf-8') as f:
                    vanilla_profile = json.load(f)
                
                for library in vanilla_profile.get("libraries", []):
                    if "downloads" in library and "artifact" in library["downloads"]:
                        artifact = library["downloads"]["artifact"]
                        lib_path = libraries_dir / artifact["path"]
                        if lib_path.exists():
                            classpath_parts.append(str(lib_path))
                    elif "name" in library:
                        lib_name = library["name"]
                        parts = lib_name.split(":")
                        if len(parts) >= 3:
                            group_id, artifact_id, version = parts[0], parts[1], parts[2]
                            group_path = group_id.replace(".", "/")
                            jar_name = f"{artifact_id}-{version}.jar"
                            jar_path = libraries_dir / group_path / artifact_id / version / jar_name
                            if jar_path.exists():
                                classpath_parts.append(str(jar_path))
            
            # Fabric libraries
            for library in fabric_profile.get("libraries", []):
                lib_name = library.get("name")
                if not lib_name:
                    continue
                
                parts = lib_name.split(":")
                if len(parts) != 3:
                    continue
                
                group_id, artifact_id, version = parts[0], parts[1], parts[2]
                group_path = group_id.replace(".", "/")
                jar_name = f"{artifact_id}-{version}.jar"
                jar_path = libraries_dir / group_path / artifact_id / version / jar_name
                
                if jar_path.exists():
                    classpath_parts.append(str(jar_path))
            
            # Minecraft client JAR
            mc_jar = self.minecraft_dir / "versions" / MCVERSION / f"{MCVERSION}.jar"
            if mc_jar.exists():
                classpath_parts.append(str(mc_jar))
            else:
                raise Exception(f"Minecraft JAR not found!")
            
            self.log_print(f"Classpath: {len(classpath_parts)} entries")
            
            classpath_separator = ";" if os.name == "nt" else ":"
            classpath = classpath_separator.join(classpath_parts)
            
            # Natives directory
            natives_dir = self.minecraft_dir / "natives"
            natives_dir.mkdir(exist_ok=True)
            
            # Assets directory
            assets_dir = self.minecraft_dir / "assets"
            
            # Launch command
            launch_cmd = [
                str(java_exe),
                f"-Xmx{ram}G",
                f"-Xms{ram}G",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+UseG1GC",
                "-XX:G1NewSizePercent=20",
                "-XX:G1ReservePercent=20",
                "-XX:MaxGCPauseMillis=50",
                "-XX:G1HeapRegionSize=32M",
                "-XX:+AlwaysPreTouch",
                "-XX:+DisableExplicitGC",
                "-XX:+ParallelRefProcEnabled",
                f"-Djava.library.path={natives_dir}",
                "-cp",
                classpath,
                main_class,
                "--username", username,
                "--version", version_name,
                "--gameDir", str(self.minecraft_dir),
                "--assetsDir", str(assets_dir),
                "--assetIndex", self.asset_index_id,  # FIXED: Use correct assetIndex
                "--accessToken", "0",
                "--userType", "legacy"
            ]
            
            self.log_print(f"RAM: {ram}GB | Mods: {mod_count}")
            self.log_print(f"AssetIndex: {self.asset_index_id}")
            
            # Create log file
            logs_dir = self.minecraft_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = logs_dir / f"launcher_{timestamp}.log"
            
            self.log_print(f"Game log: {log_file.name}")
            
            self.update_status(f"Starting game ({mod_count} mods, {estimated_time})...", "#ffaa00")
            self.update_progress(0.8, f"Starting game...")
            
            import time
            start_time = time.time()
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"=== Gama Launcher - Game Launch Log ===\n")
                log.write(f"Timestamp: {datetime.now()}\n")
                log.write(f"Tier: {tier}\n")
                log.write(f"RAM: {ram}G\n")
                log.write(f"Mods: {mod_count}\n")
                log.write(f"Shaders: {shaders_enabled}\n")
                log.write(f"AssetIndex: {self.asset_index_id}\n")
                log.write(f"\n=== Game Output ===\n")
                log.flush()
                
                process = subprocess.Popen(
                    launch_cmd,
                    cwd=str(self.minecraft_dir),
                    stdout=log,
                    stderr=log,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
            
            elapsed_final = int(time.time() - start_time)
            
            self.update_status(f"Game launched! Window appearing soon...", "#00ff00")
            self.update_progress(0.95, f"Game started ({elapsed_final}s)")
            
            self.log_print(f"✓ Game started! ({elapsed_final}s)")
            self.log_print("You can minimize this window")
            
            # Monitor game process
            threading.Thread(
                target=self.monitor_game_process,
                args=(process, log_file),
                daemon=True
            ).start()
            
        except Exception as e:
            error_msg = str(e)
            self.update_status(f"Launch error: {error_msg}", "#ff0000")
            self.update_progress(0, "Error")
            self.launch_btn.configure(state="normal", text="🚀 LAUNCH GAME")
            
            self.log_print("="*40)
            self.log_print("ERROR!")
            self.log_print(f"Error: {error_msg}")
            self.log_print("="*40)
            
            import traceback
            traceback.print_exc()
    
    def monitor_game_process(self, process, log_file):
        """Monitor game process and update UI when closed"""
        try:
            import time
            start_time = time.time()
            
            exit_code = process.wait()
            
            play_time = int(time.time() - start_time)
            play_mins = play_time // 60
            play_secs = play_time % 60
            
            if exit_code == 0:
                self.update_status(
                    f"Game closed normally (played {play_mins}m {play_secs}s). Ready to launch!",
                    "#00cc00"
                )
                self.update_progress(1.0, f"Session: {play_mins}m {play_secs}s")
                self.log_print(f"\n✓ Game closed (played {play_mins}m {play_secs}s)")
            else:
                self.update_status(f"Game crashed (exit {exit_code}). Check {log_file.name}", "#ff4444")
                self.update_progress(0, "Crashed")
                self.log_print(f"\n✗ Game crashed (exit {exit_code})")
                self.log_print(f"Check log: {log_file.name}")
            
            self.launch_btn.configure(state="normal", text="🚀 LAUNCH GAME")
            self.log_print("Ready to launch again!")
            
        except Exception as e:
            self.log_print(f"Error monitoring process: {e}")
            self.launch_btn.configure(state="normal", text="🚀 LAUNCH GAME")
            self.update_progress(0, "Ready")


if __name__ == "__main__":
    print("="*60)
    print("GAMA SERVER LAUNCHER v2.1.0")
    print("="*60)
    print("Features:")
    print(" • New tier system: Very Low/Low/Medium/High/Very High/Ultra")
    print(" • Shader checkbox (tier-gated)")
    print(" • Fixed vanilla sounds (full asset download)")
    print(" • System recommendations (with/without shaders)")
    print(" • Log window for real-time feedback")
    print(" • Smart path detection (installed vs portable)")
    print("="*60)
    print()
    
    app = GamaLauncher()
    app.mainloop()

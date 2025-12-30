"""
Pre-configure Minecraft server list
Adds Gama server to multiplayer menu automatically
"""

import struct
from pathlib import Path
from typing import List, Dict


class MinecraftServerList:
    """Manages Minecraft servers.dat file (NBT format)"""
    
    def __init__(self, minecraft_dir: Path):
        self.minecraft_dir = minecraft_dir
        self.servers_file = minecraft_dir / "servers.dat"
    
    def create_servers_dat(self, servers: List[Dict]):
        """
        Create servers.dat with pre-configured servers
        
        Args:
            servers: List of dicts with 'name' and 'ip' keys
        """
        try:
            # Simple NBT writer for servers.dat
            # Format: TAG_Compound with TAG_List of TAG_Compounds
            
            with open(self.servers_file, 'wb') as f:
                # TAG_Compound (root)
                f.write(b'\x0a')  # TAG_Compound
                self._write_string(f, '')  # Empty root name
                
                # TAG_List "servers"
                f.write(b'\x09')  # TAG_List
                self._write_string(f, 'servers')
                f.write(b'\x0a')  # List type: TAG_Compound
                f.write(struct.pack('>i', len(servers)))  # Number of servers
                
                # Write each server
                for server in servers:
                    # Server TAG_Compound
                    
                    # Server name (TAG_String)
                    f.write(b'\x08')  # TAG_String
                    self._write_string(f, 'name')
                    self._write_string(f, server['name'])
                    
                    # Server IP (TAG_String)
                    f.write(b'\x08')  # TAG_String
                    self._write_string(f, 'ip')
                    self._write_string(f, server['ip'])
                    
                    # Hide address (TAG_Byte) - optional, set to 0 (show)
                    f.write(b'\x01')  # TAG_Byte
                    self._write_string(f, 'hideAddress')
                    f.write(b'\x00')  # False
                    
                    # End of server compound
                    f.write(b'\x00')  # TAG_End
                
                # End of root compound
                f.write(b'\x00')  # TAG_End
            
            return True
            
        except Exception as e:
            print(f"Error creating servers.dat: {e}")
            return False
    
    def _write_string(self, f, string: str):
        """Write NBT string (length + UTF-8 bytes)"""
        encoded = string.encode('utf-8')
        f.write(struct.pack('>H', len(encoded)))  # 2-byte length
        f.write(encoded)
    
    def add_gama_server(self):
        """Add Gama server to the list"""
        servers = [
            {
                'name': '§c§lGAMA KLUB §7• §fSurvival Server',
                'ip': 'gamaklub.ggwp.cc'
            }
        ]
        
        # Only create if file doesn't exist (don't overwrite user's servers)
        if not self.servers_file.exists():
            success = self.create_servers_dat(servers)
            if success:
                print("✓ Gama server added to multiplayer list")
                return True
            else:
                print("⚠️  Could not add server to list")
                return False
        else:
            print("✓ Using existing server list")
            return True

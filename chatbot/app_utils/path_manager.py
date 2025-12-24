"""
Path management utility to eliminate sys.path manipulation.
This module provides a cleaner way to handle imports from different thor versions.
"""
import sys
from pathlib import Path
from typing import Optional
import importlib.util


class PathManager:
    """
    Manages Python path and imports without directly manipulating sys.path.
    Provides a cleaner interface for loading modules from different thor versions.
    """
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.resolve()
        self.atlas_root = self.base_dir.parent
        self.thor_1_0_dir = self.atlas_root / "thor-1.0"
        self.thor_1_1_dir = self.atlas_root / "thor-1.1"
        self.chatbot_dir = self.base_dir
        
        # Track which thor version is currently active
        self._active_thor = 'thor-1.1'
    
    def get_thor_dir(self, version: str = 'thor-1.1') -> Path:
        """Get the path to a specific thor version directory."""
        if version == 'thor-1.0':
            return self.thor_1_0_dir
        elif version == 'thor-1.1':
            return self.thor_1_1_dir
        else:
            raise ValueError(f"Unknown thor version: {version}")
    
    def load_module_from_path(self, module_name: str, file_path: Path) -> object:
        """
        Load a module from a specific file path without modifying sys.path.
        
        This is a safer alternative to sys.path manipulation.
        """
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    def import_from_thor(self, module_name: str, version: str = 'thor-1.1'):
        """
        Import a module from a specific thor version.
        
        This method temporarily adds the thor directory to sys.path,
        imports the module, then restores sys.path.
        This is a compromise solution until full package restructuring.
        """
        thor_dir = self.get_thor_dir(version)
        thor_path = str(thor_dir)
        
        # Store original sys.path
        original_path = sys.path.copy()
        
        try:
            # Temporarily add thor path
            if thor_path not in sys.path:
                sys.path.insert(0, thor_path)
            
            # Import the module
            module = __import__(module_name, fromlist=[''])
            return module
        finally:
            # Restore original sys.path
            sys.path[:] = original_path
    
    def set_active_thor(self, version: str):
        """Set the active thor version for default imports."""
        if version not in ['thor-1.0', 'thor-1.1']:
            raise ValueError(f"Unknown thor version: {version}")
        self._active_thor = version
    
    def get_active_thor_dir(self) -> Path:
        """Get the directory of the currently active thor version."""
        return self.get_thor_dir(self._active_thor)


# Global instance
_path_manager = PathManager()

def get_path_manager() -> PathManager:
    """Get the global PathManager instance."""
    return _path_manager


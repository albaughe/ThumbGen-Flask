import os
from pathlib import Path
from PIL import Image, ImageFont
from functools import lru_cache
import platform

class ResourceManager:
    def __init__(self):
        self._images = {}  # Combined cache for backgrounds and patterns
        self._fonts = {}
        self._font_paths = {}
        
        # Resource lists
        self._background_names = []
        self._pattern_names = []
        self._font_names = []
        
        self._setup_paths()
        self._scan_resources()
    
    def _setup_paths(self):
        """Set up resource paths"""
        base_path = Path(__file__).parent.parent.absolute()
        self.paths = {
            'backgrounds': base_path / "static" / "backgrounds",
            'patterns': base_path / "static" / "patterns", 
            'fonts': base_path / "static" / "fonts"
        }
        
        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)
    
    def _scan_resources(self):
        """Scan directories for available resources"""
        self._background_names = self._scan_directory(self.paths['backgrounds'], {".png", ".jpg", ".jpeg", ".gif"})
        self._pattern_names = self._scan_directory(self.paths['patterns'], {".png", ".jpg", ".jpeg", ".gif"})
        self._font_names = self._scan_directory(self.paths['fonts'], {".ttf", ".otf"})
        
        # Store font paths
        for font_name in self._font_names:
            for ext in [".ttf", ".otf"]:
                font_path = self.paths['fonts'] / f"{font_name}{ext}"
                if font_path.exists():
                    self._font_paths[font_name] = str(font_path)
                    break
        
        print(f"Found {len(self._background_names)} backgrounds, {len(self._pattern_names)} patterns, {len(self._font_names)} fonts")
    
    def _scan_directory(self, directory_path, extensions):
        """Scan directory for files with given extensions"""
        names = []
        try:
            if directory_path.exists():
                for file_path in directory_path.glob("*"):
                    if file_path.suffix.lower() in extensions:
                        names.append(file_path.stem)
        except Exception as e:
            print(f"Error scanning {directory_path}: {e}")
        return sorted(names)
    
    @lru_cache(maxsize=64)
    def get_image(self, name, image_type):
        """Get image (background or pattern) with caching"""
        if not name or name == "None":
            return None
        
        cache_key = f"{image_type}_{name}"
        if cache_key in self._images:
            return self._images[cache_key]
        
        # Load image
        try:
            directory = self.paths[image_type + 's']  # backgrounds, patterns
            for ext in [".png", ".jpg", ".jpeg", ".gif"]:
                file_path = directory / f"{name}{ext}"
                if file_path.exists():
                    image = Image.open(file_path).convert("RGBA")
                    # Only optimize background images, not patterns
                    if image_type == 'background':
                        max_size = 2048
                        if image.width > max_size or image.height > max_size:
                            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    self._images[cache_key] = image
                    return image
        except Exception as e:
            print(f"Error loading {image_type} {name}: {e}")
        
        return None
    
    def get_background_image(self, name):
        """Get background image"""
        return self.get_image(name, 'background')
    
    def get_pattern_image(self, name):
        """Get pattern image"""
        return self.get_image(name, 'pattern')
    
    @lru_cache(maxsize=128)
    def get_pil_font(self, font_name, size):
        """Get PIL font with caching"""
        cache_key = f"{font_name}_{size}"
        
        if cache_key in self._fonts:
            return self._fonts[cache_key]
        
        font = None
        
        try:
            # Try custom font first
            if font_name in self._font_paths:
                font = ImageFont.truetype(self._font_paths[font_name], size)
            else:
                # Try system font
                font = self._get_system_font(font_name, size)
            
        except Exception as e:
            print(f"Font loading error for {font_name}: {e}")
            font = ImageFont.load_default()
        
        self._fonts[cache_key] = font
        
        # Limit cache size
        if len(self._fonts) > 150:
            old_keys = list(self._fonts.keys())[:50]
            for key in old_keys:
                del self._fonts[key]
        
        return font
    
    def _get_system_font(self, font_name, size):
        """Get system font with fallbacks"""
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            pass
        
        # Platform-specific fallbacks
        system = platform.system().lower()
        fallbacks = self._get_platform_fallbacks(system, font_name)
        
        for fallback in fallbacks:
            try:
                return ImageFont.truetype(fallback, size)
            except OSError:
                continue
        
        return ImageFont.load_default()
    
    @lru_cache(maxsize=16)
    def _get_platform_fallbacks(self, system, font_name):
        """Get platform-specific font fallbacks"""
        if system == "windows":
            fallbacks = [
                "arial.ttf", "calibri.ttf", "segoeui.ttf", "tahoma.ttf",
                "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf"
            ]
            if font_name.lower() == "impact":
                fallbacks.insert(0, "impact.ttf")
                fallbacks.insert(0, "C:/Windows/Fonts/impact.ttf")
                
        elif system == "darwin":  # macOS
            fallbacks = [
                "Arial.ttc", "Helvetica.ttc", "Arial.ttf",
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ]
            if font_name.lower() == "impact":
                fallbacks.insert(0, "Impact.ttf")
                
        else:  # Linux
            fallbacks = [
                "DejaVuSans.ttf", "liberation-sans.ttf", "Ubuntu-R.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ]
        
        return fallbacks
    
    def get_background_names(self):
        return self._background_names
    
    def get_pattern_names(self):
        return self._pattern_names
    
    def get_font_names(self):
        return self._font_names
    
    def refresh_resources(self):
        """Refresh resource lists"""
        print("Refreshing resources...")
        
        self._images.clear()
        self._fonts.clear()
        self._scan_resources()
        
        # Clear LRU caches
        self.get_image.cache_clear()
        self.get_pil_font.cache_clear()
        self._get_platform_fallbacks.cache_clear()
        
        print("Resources refreshed")
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return {
            "images_cached": len(self._images),
            "fonts_cached": len(self._fonts),
            "image_cache_info": self.get_image.cache_info(),
            "font_cache_info": self.get_pil_font.cache_info()
        }
#python#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    from core.thumbnail import ThumbnailGenerator
    print("✅ ThumbnailGenerator import successful")
    
    from resources.resource_manager import ResourceManager
    print("✅ ResourceManager import successful")
    
    # Test initialization
    rm = ResourceManager()
    print("✅ ResourceManager initialized")
    
    tg = ThumbnailGenerator(rm)
    print("✅ ThumbnailGenerator initialized")
    
    print("\n🎉 All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
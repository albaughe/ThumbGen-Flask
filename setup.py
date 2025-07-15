#!/usr/bin/env python3
"""
Setup script for Flask Thumbnail Generator
This script creates the necessary directory structure and files.
"""

import os
from pathlib import Path

def create_project_structure():
    """Create the complete project directory structure"""
    
    # Define the project structure
    directories = [
        "static/backgrounds",
        "static/patterns", 
        "static/fonts",
        "templates",
        "uploads"
    ]
    
    # Create directories
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Create templates/index.html (copy your existing HTML content here)
    template_content = """<!-- Place your index.html content here -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thumbnail Generator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #23272b !important; color: #f5f6fa !important; }
        .card { background: #2d3136 !important; border: 1.5px solid #444 !important; color: #f5f6fa !important; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1>Flask Thumbnail Generator</h1>
        <p>Please replace this file with your complete index.html content.</p>
        <p>Available backgrounds: {{ backgrounds|length }}</p>
        <p>Available patterns: {{ patterns|length }}</p>
        <p>Available fonts: {{ fonts|length }}</p>
    </div>
</body>
</html>"""
    
    with open("templates/index.html", "w") as f:
        f.write(template_content)
    print("✓ Created basic templates/index.html (replace with your full HTML)")
    
    # Create requirements.txt
    requirements = """Flask==2.3.3
Pillow==10.0.1
Werkzeug==2.3.7"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✓ Created requirements.txt")
    
    # Create .gitignore
    gitignore = """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
uploads/
instance/
.webassets-cache
.coverage
htmlcov/
.pytest_cache/
.DS_Store
Thumbs.db"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore)
    print("✓ Created .gitignore")
    
    # Create README.md
    readme = """# Flask Thumbnail Generator

A web application for generating custom thumbnails with text overlays, background images, and patterns.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Add your resources:
   - Place background images in `static/backgrounds/`
   - Place pattern images in `static/patterns/`
   - Place custom fonts in `static/fonts/`

3. Replace `templates/index.html` with your complete HTML file

4. Run the application:
   ```bash
   python app.py
   ```

5. Open http://localhost:5000 in your browser

## File Structure

```
├── app.py                 # Main Flask application
├── resource_manager.py    # Resource management
├── thumbnail.py          # Thumbnail generation logic
├── image_utils.py        # Image utility functions
├── templates/
│   └── index.html        # Web interface
├── static/
│   ├── backgrounds/      # Background images
│   ├── patterns/         # Pattern overlays
│   └── fonts/           # Custom fonts
└── uploads/             # Temporary uploads
```

## Features

- Individual and batch thumbnail generation
- Real-time preview with caching
- Custom fonts, backgrounds, and patterns
- Text positioning and styling
- Background image and pattern overlays
- Optimized performance with LRU caching
"""
    
    with open("README.md", "w") as f:
        f.write(readme)
    print("✓ Created README.md")
    
    print("\n" + "="*50)
    print("PROJECT SETUP COMPLETE!")
    print("="*50)
    print("\nNext steps:")
    print("1. Copy your Python files to this directory:")
    print("   - resource_manager.py")
    print("   - thumbnail.py") 
    print("   - image_utils.py")
    print("   - app.py (main Flask file)")
    print("\n2. Replace templates/index.html with your complete HTML file")
    print("\n3. Add your resources:")
    print("   - Background images → static/backgrounds/")
    print("   - Pattern images → static/patterns/")
    print("   - Custom fonts → static/fonts/")
    print("\n4. Install dependencies: pip install -r requirements.txt")
    print("5. Run: python app.py")

if __name__ == "__main__":
    create_project_structure()
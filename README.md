# Flask Thumbnail Generator

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
# ThumbGen-Flask
# ThumbGen-Flask

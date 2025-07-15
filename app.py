from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image
import io
import base64
import os
import zipfile
from datetime import datetime
from werkzeug.utils import secure_filename
import hashlib
import threading
import time

from core.thumbnail import ThumbnailGenerator
from resources.resource_manager import ResourceManager

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global instances
resource_manager = ResourceManager()
generator = ThumbnailGenerator(resource_manager)

# Simplified cache
class SimpleCache:
    def __init__(self, max_size=100, ttl=300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache and time.time() - self.access_times[key] < self.ttl:
                self.access_times[key] = time.time()
                return self.cache[key]
            elif key in self.cache:
                del self.cache[key], self.access_times[key]
        return None
    
    def set(self, key, value):
        with self.lock:
            if len(self.cache) >= self.max_size:
                oldest = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest], self.access_times[oldest]
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self.access_times.clear()

preview_cache = SimpleCache()

def create_cache_key(form_data):
    """Create cache key from form data"""
    key_fields = [
        'text', 'start_number', 'font_name', 'font_size', 'text_color', 'text_alignment',
        'background_color', 'background_opacity', 'background_image_enabled', 'background_image',
        'bg_image_scale', 'bg_image_x_offset', 'bg_image_y_offset', 'pattern_enabled',
        'pattern_overlay', 'pattern_color_enabled', 'pattern_color', 'pattern_opacity',
        'pattern_scale', 'pattern_x_offset', 'pattern_y_offset', 'text_margins',
        'text_x_offset', 'text_y_offset', 'line_spacing_factor', 'text_stroke_enabled',
        'text_stroke_width', 'text_stroke_color', 'text_box_enabled', 'text_box_color',
        'text_box_padding', 'text_box_opacity', 'batch_count', 'filename_base'
    ]
    values = [str(form_data.get(field, '')) for field in key_fields]
    return hashlib.md5('|'.join(values).encode()).hexdigest()

def parse_settings(form_data):
    """Parse and validate form settings"""
    def safe_int(value, default):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def hex_to_rgba(hex_color):
        if not hex_color or not hex_color.startswith('#'):
            return (255, 255, 255, 255)
        try:
            hex_color = hex_color[1:]
            return (
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16), 
                int(hex_color[4:6], 16),
                255
            )
        except ValueError:
            return (255, 255, 255, 255)
    
    return {
        'text': form_data.get('text', 'Week ^ Overview'),
        'filename_base': form_data.get('filename_base', 'output'),
        'text_color': hex_to_rgba(form_data.get('text_color', '#ffffff')),
        'text_alignment': form_data.get('text_alignment', 'center'),
        'font_name': form_data.get('font_name', 'Arial'),
        'font_size': safe_int(form_data.get('font_size'), 100),
        'text_margins': safe_int(form_data.get('text_margins'), 100),
        'text_x_offset': safe_int(form_data.get('text_x_offset'), 0),
        'text_y_offset': safe_int(form_data.get('text_y_offset'), 0),
        'line_spacing_factor': safe_int(form_data.get('line_spacing_factor'), 30) / 100.0,
        
        'text_stroke_enabled': form_data.get('text_stroke_enabled') == 'on',
        'text_stroke_width': safe_int(form_data.get('text_stroke_width'), 2),
        'text_stroke_color': hex_to_rgba(form_data.get('text_stroke_color', '#000000')),
        'text_box_enabled': form_data.get('text_box_enabled') == 'on',
        'text_box_color': hex_to_rgba(form_data.get('text_box_color', '#000000')),
        'text_box_padding': safe_int(form_data.get('text_box_padding'), 20),
        'text_box_opacity': safe_int(form_data.get('text_box_opacity'), 100),
        
        'background_color': hex_to_rgba(form_data.get('background_color', '#d73f09')),
        'background_opacity': safe_int(form_data.get('background_opacity'), 100),
        'background_image_enabled': form_data.get('background_image_enabled', 'off') == 'on',
        'background_image': form_data.get('background_image', 'None'),
        'bg_image_scale': safe_int(form_data.get('bg_image_scale'), 100),
        'bg_image_x_offset': safe_int(form_data.get('bg_image_x_offset'), 0),
        'bg_image_y_offset': safe_int(form_data.get('bg_image_y_offset'), 0),
        
        'pattern_enabled': form_data.get('pattern_enabled') == 'on',
        'pattern_overlay': form_data.get('pattern_overlay', 'None'),
        'pattern_color_enabled': form_data.get('pattern_color_enabled') == 'on',
        'pattern_color': hex_to_rgba(form_data.get('pattern_color', '#ffffff')),
        'pattern_opacity': safe_int(form_data.get('pattern_opacity'), 100),
        'pattern_scale': safe_int(form_data.get('pattern_scale'), 300),
        'pattern_x_offset': safe_int(form_data.get('pattern_x_offset'), 0),
        'pattern_y_offset': safe_int(form_data.get('pattern_y_offset'), 0),
        
        'start_number': safe_int(form_data.get('start_number'), 1),
        'batch_count': safe_int(form_data.get('batch_count'), 1)
    }

def apply_settings(settings):
    """Apply settings to generator"""
    # Text settings
    generator.text_color = settings['text_color']
    generator.text_alignment = settings['text_alignment']
    generator.font_name = settings['font_name']
    generator.font_size = settings['font_size']
    generator.text_margins = settings['text_margins']
    generator.text_x_offset = settings['text_x_offset']
    generator.text_y_offset = settings['text_y_offset']
    generator.line_spacing_factor = settings['line_spacing_factor']
    
    # Text accessibility
    generator.text_stroke_width = settings['text_stroke_width'] if settings['text_stroke_enabled'] else 0
    generator.text_stroke_color = settings['text_stroke_color']
    generator.text_box_enabled = settings['text_box_enabled']
    
    box_color = settings['text_box_color']
    opacity = settings['text_box_opacity']
    generator.text_box_color = box_color[:3] + (int(255 * opacity / 100),)
    generator.text_box_padding = settings['text_box_padding']
    
    # Background
    generator.background_color = settings['background_color']
    generator.background_opacity = settings['background_opacity']
    generator.bg_image_scale = settings['bg_image_scale']
    generator.bg_image_x_offset = settings['bg_image_x_offset']
    generator.bg_image_y_offset = settings['bg_image_y_offset']
    
    # Background image
    if settings['background_image_enabled']:
        bg_img = settings['background_image']
        if bg_img and bg_img not in ['None', 'Custom', '']:
            generator.background_image = resource_manager.get_background_image(bg_img)  # type: ignore
        else:
            available_backgrounds = resource_manager.get_background_names()
            if available_backgrounds:
                generator.background_image = resource_manager.get_background_image(available_backgrounds[0])  # type: ignore
            else:
                generator.background_image = None
    else:
        generator.background_image = None
    
    # Pattern
    if settings['pattern_enabled']:
        pattern = settings['pattern_overlay']
        if pattern:
            generator.current_pattern = resource_manager.get_pattern_image(pattern)  # type: ignore
        else:
            generator.current_pattern = None
    else:
        generator.current_pattern = None
    
    generator.pattern_color_enabled = settings['pattern_color_enabled']
    generator.pattern_color = settings['pattern_color']
    generator.pattern_opacity = settings['pattern_opacity']
    generator.pattern_scale = settings['pattern_scale']
    generator.pattern_x_offset = settings['pattern_x_offset']
    generator.pattern_y_offset = settings['pattern_y_offset']
    
    generator.filename_base = settings['filename_base']

@app.route('/')
def index():
    return render_template('index.html', 
                         backgrounds=resource_manager.get_background_names(),
                         patterns=resource_manager.get_pattern_names(),
                         fonts=resource_manager.get_font_names())

@app.route('/preview', methods=['POST'])
def preview():
    try:
        form_data = request.form.to_dict()
        
        # Parse settings
        settings = parse_settings(form_data)
        
        # Apply settings to generator
        apply_settings(settings)
        
        # Generate preview
        text = settings.get('text', 'Week Overview')
        preview_data, _ = generator.generate_thumbnail(text, 1, 1280, 720)
        
        # Convert to base64
        img_buffer = io.BytesIO()
        preview_data.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/individual', methods=['POST'])
def download_individual():
    try:
        form_data = request.form.to_dict()
        
        # Parse settings
        settings = parse_settings(form_data)
        
        # Apply settings to generator
        apply_settings(settings)
        
        # Generate thumbnail
        text = settings.get('text', 'Week Overview')
        thumbnail, _ = generator.generate_thumbnail(text, 1, 1280, 720)
        
        # Save to buffer
        img_buffer = io.BytesIO()
        thumbnail.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return send_file(
            img_buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'thumbnail_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate', methods=['POST'])
def generate_batch():
    try:
        form_data = request.form.to_dict()
        
        # Debug: log what we received
        print("Received form data:", form_data)
        print("Batch mode:", form_data.get('batch_mode'))
        print("Start number:", form_data.get('start_number'))
        print("Batch count:", form_data.get('batch_count'))
        print("Filename base:", form_data.get('filename_base'))
        
        # Parse settings
        settings = parse_settings(form_data)
        
        # Get batch parameters
        start_number = int(form_data.get('start_number', 1))
        batch_count = int(form_data.get('batch_count', 1))
        filename_base = form_data.get('filename_base', 'Thumbnail')
        text_template = form_data.get('text', 'Week Overview')
        
        # Apply settings to generator
        apply_settings(settings)
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i in range(batch_count):
                # Replace ^ with current number in text
                current_text = text_template.replace('^', str(start_number + i))
                
                # Generate thumbnail
                thumbnail, _ = generator.generate_thumbnail(current_text, start_number + i, 1280, 720)
                
                # Create filename
                current_filename = filename_base.replace('^', str(start_number + i))
                filename = f'{current_filename}_{start_number + i}.png'
                
                # Save to ZIP
                img_buffer = io.BytesIO()
                thumbnail.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                zip_file.writestr(filename, img_buffer.getvalue())
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'thumbnails_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload_background', methods=['POST'])
def upload_background():
    try:
        if 'background_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['background_file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'error': 'Invalid file type'})
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        img = Image.open(filepath).convert("RGBA")
        max_size = 2048
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        generator.background_image = img  # type: ignore
        preview_cache.clear()
        
        return jsonify({'success': True, 'message': 'Background uploaded successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    preview_cache.clear()
    return jsonify({'success': True, 'message': 'Cache cleared'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
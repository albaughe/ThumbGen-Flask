from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache

class ThumbnailGenerator:
    def __init__(self, resource_manager):
        self.resources = resource_manager
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize default settings"""
        # Background settings
        self.background_image = None
        self.background_color = (215, 63, 9, 255)
        self.background_opacity = 100
        self.bg_image_scale = 100
        self.bg_image_x_offset = 0
        self.bg_image_y_offset = 0
        
        # Pattern settings
        self.current_pattern = None
        self.pattern_opacity = 100
        self.pattern_scale = 40
        self.pattern_x_offset = 0
        self.pattern_y_offset = 0
        self.pattern_color = (255, 255, 255, 255)
        self.pattern_color_enabled = False
        
        # Text settings
        self.text_color = (255, 255, 255, 255)
        self.text_alignment = "center"
        self.text_margins = 100
        self.text_x_offset = 0
        self.text_y_offset = 0
        self.line_spacing_factor = 0.3
        
        # Text accessibility
        self.text_stroke_width = 0
        self.text_stroke_color = (0, 0, 0, 255)
        self.text_box_enabled = False
        self.text_box_color = (0, 0, 0, 255)
        self.text_box_padding = 20
        
        # Font info
        self.font_name = "Arial"
        self.font_size = 100
        
        # Filename
        self.filename_base = "output"
    
    @lru_cache(maxsize=128)
    def _wrap_text(self, text, font_name, font_size, max_width):
        """Wrap text to fit width"""
        font = self.resources.get_pil_font(font_name, font_size)
        temp_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(temp_img)
        
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            words = line.split()
            current_line = []
            
            for word in words:
                test_line = current_line + [word]
                test_text = ' '.join(test_line)
                
                left, top, right, bottom = draw.textbbox((0, 0), test_text, font=font)
                text_width = right - left
                
                if text_width > max_width and current_line:
                    processed_lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    current_line = test_line
            
            if current_line:
                processed_lines.append(' '.join(current_line))
        
        return tuple(processed_lines)
    
    def generate_thumbnail(self, text, number, width=1280, height=720):
        """Generate thumbnail"""
        display_text = text.replace('^', str(number))
        
        # Start with base image
        img = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
        
        # Add layers
        img = self._add_background_color(img, width, height)
        img = self._add_background_image(img, width, height)
        img = self._add_pattern(img, width, height)
        img = self._add_text(img, display_text, width, height)
        
        filename = f"{self.filename_base}{number}"
        return img, filename
    
    def _add_background_color(self, img, width, height):
        """Add solid background color"""
        bg_color_img = Image.new("RGBA", (width, height), color=self.background_color[:3] + (255,))
        return Image.alpha_composite(img, bg_color_img)
    
    def _add_background_image(self, img, width, height):
        """Add background image with opacity"""
        if not self.background_image:
            return img
        
        # Calculate dimensions
        scale_factor = self.bg_image_scale / 100.0
        bg_width = int(width * scale_factor)
        bg_height = int(height * scale_factor)
        
        # Resize image
        resample = Image.Resampling.LANCZOS if scale_factor < 1 else Image.Resampling.BILINEAR
        resized_bg = self.background_image.resize((bg_width, bg_height), resample)
        
        # Create canvas and position image
        bg_canvas = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
        x_pos = (width - bg_width) // 2 + self.bg_image_x_offset
        y_pos = (height - bg_height) // 2 + self.bg_image_y_offset
        bg_canvas.paste(resized_bg, (x_pos, y_pos), resized_bg)
        
        # Apply opacity
        if self.background_opacity < 100:
            r, g, b, a = bg_canvas.split()
            opacity_factor = self.background_opacity / 100.0
            a = a.point(lambda i: int(i * opacity_factor))
            bg_canvas = Image.merge('RGBA', (r, g, b, a))
        
        return Image.alpha_composite(img, bg_canvas)
    
    def _add_pattern(self, img, width, height):
        """Add pattern overlay"""
        if not self.current_pattern:
            return img
        
        # Get original pattern dimensions
        orig_width, orig_height = self.current_pattern.size  # type: ignore
        
        # Calculate scale factor based on pattern scale setting
        scale_factor = self.pattern_scale / 100.0
        
        # Calculate new dimensions while preserving aspect ratio
        if scale_factor != 1.0:
            new_width = int(orig_width * scale_factor)
            new_height = int(orig_height * scale_factor)
            # Resize pattern
            resample = Image.Resampling.LANCZOS if scale_factor < 1 else Image.Resampling.BILINEAR
            pattern = self.current_pattern.resize((new_width, new_height), resample)
        else:
            pattern = self.current_pattern.copy()
            new_width, new_height = orig_width, orig_height
        
        # Create pattern canvas and position
        pattern_canvas = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
        
        # Position relative to frame size, not pattern size
        # Use frame-relative positioning so small patterns can still move significantly
        x_pos = (width - new_width) // 2 + self.pattern_x_offset
        y_pos = (height - new_height) // 2 + self.pattern_y_offset
        pattern_canvas.paste(pattern, (x_pos, y_pos), pattern)
        
        # Apply color tint if enabled
        if self.pattern_color_enabled:
            r, g, b, a = pattern_canvas.split()
            tinted_pattern = Image.new('RGBA', pattern_canvas.size, self.pattern_color[:3] + (0,))
            tinted_pattern.putalpha(a)
            pattern_canvas = tinted_pattern
        
        # Apply opacity
        if self.pattern_opacity < 100:
            r, g, b, a = pattern_canvas.split()
            opacity_factor = self.pattern_opacity / 100.0
            # Scale the alpha values by the opacity factor
            # This preserves the original pattern's alpha structure but scales it
            a = a.point(lambda i: int(i * opacity_factor))
            pattern_canvas = Image.merge('RGBA', (r, g, b, a))
        
        return Image.alpha_composite(img, pattern_canvas)
    
    def _add_text(self, img, display_text, width, height):
        """Add text overlay"""
        draw = ImageDraw.Draw(img)
        font = self.resources.get_pil_font(self.font_name, self.font_size)
        
        # Get wrapped text
        max_text_width = width - (self.text_margins * 2)
        lines = self._wrap_text(display_text, self.font_name, self.font_size, max_text_width)
        
        # Calculate text layout
        line_spacing = int(self.font_size * self.line_spacing_factor)
        text_height = len(lines) * (self.font_size + line_spacing) - line_spacing
        
        # Determine y_position based on alignment
        align = self.text_alignment
        if align in ("top_left", "top_center", "top_right"):
            y_position = self.text_margins + self.text_y_offset
        elif align in ("bottom_left", "bottom_center", "bottom_right"):
            y_position = height - self.text_margins - text_height + self.text_y_offset
        else:  # center, left, right
            y_position = (height - text_height) // 2 + self.text_y_offset
        
        # Calculate max line width for background box
        max_line_width = 0
        if self.text_box_enabled:
            for line in lines:
                left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
                max_line_width = max(max_line_width, right - left)
        
        # Draw background box if enabled
        if self.text_box_enabled:
            self._draw_text_box(draw, lines, max_line_width, width, height, y_position)
        
        # Draw text with stroke
        text_color = self.text_color[:3] + (255,)
        stroke_color = self.text_stroke_color[:3] + (255,)
        stroke_width = self.text_stroke_width
        
        for line in lines:
            x_position = self._calculate_text_x_position(line, font, draw, width, align)
            draw.text(
                (x_position, y_position),
                line,
                font=font,
                fill=text_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )
            y_position += self.font_size + line_spacing
        
        return img

    def _calculate_text_x_position(self, line, font, draw, width, align=None):
        """Calculate X position based on alignment"""
        if align is None:
            align = self.text_alignment
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        line_width = right - left
        
        if align in ("top_left", "left", "bottom_left"):
            return self.text_margins + self.text_x_offset
        elif align in ("top_center", "center", "bottom_center"):
            return (width - line_width) // 2 + self.text_x_offset
        elif align in ("top_right", "right", "bottom_right"):
            return width - self.text_margins - line_width + self.text_x_offset
        else:
            return (width - line_width) // 2 + self.text_x_offset
    
    def _draw_text_box(self, draw, lines, max_line_width, width, height, y_position):
        """Draw text background box"""
        # Position relative to frame size, not font size
        
        # Calculate box dimensions
        if self.text_alignment == "center":
            box_x = (width - max_line_width) // 2 - self.text_box_padding + self.text_x_offset
        elif self.text_alignment == "left":
            box_x = self.text_margins - self.text_box_padding + self.text_x_offset
        else:  # right
            box_x = width - self.text_margins - max_line_width - self.text_box_padding + self.text_x_offset
        
        box_y = y_position - self.text_box_padding
        box_width = max_line_width + (2 * self.text_box_padding)
        box_height = (len(lines) * (self.font_size + int(self.font_size * self.line_spacing_factor)) - 
                     int(self.font_size * self.line_spacing_factor) + (2 * self.text_box_padding))
        
        # Draw box
        if len(self.text_box_color) > 3 and self.text_box_color[3] < 255:
            # Semi-transparent box
            overlay = Image.new('RGBA', (box_width, box_height), self.text_box_color)
            img = draw._image
            img.paste(overlay, (box_x, box_y), overlay)
        else:
            # Opaque box
            draw.rectangle([box_x, box_y, box_x + box_width, box_y + box_height], 
                         fill=self.text_box_color)
"""
Image Processor - Processes images for Thor with enhanced features
"""
import base64
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import numpy as np
from datetime import datetime

class ImageProcessor:
    """Processes images and extracts information"""
    
    def __init__(self):
        self.images_dir = "processed_images"
        os.makedirs(self.images_dir, exist_ok=True)
    
    def process_image(self, image_data, filename):
        """Process uploaded image with enhanced analysis"""
        try:
            # Decode base64 image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Get image info
            width, height = image.size
            format_type = image.format
            mode = image.mode
            
            # Convert to RGB if needed for analysis
            analysis_image = image.convert('RGB')
            
            # Enhanced analysis
            dominant_colors = self._get_dominant_colors(analysis_image)
            brightness = self._get_brightness(analysis_image)
            contrast = self._get_contrast(analysis_image)
            aspect_ratio = round(width / height, 2) if height > 0 else 1
            file_size_kb = len(image_bytes) / 1024
            
            # Detect image type
            image_type = self._detect_image_type(analysis_image, width, height)
            
            # Save for reference
            save_path = os.path.join(self.images_dir, filename)
            image.save(save_path)
            
            return {
                "width": width,
                "height": height,
                "format": format_type,
                "mode": mode,
                "size_kb": round(file_size_kb, 2),
                "aspect_ratio": aspect_ratio,
                "dominant_colors": dominant_colors,
                "brightness": brightness,
                "contrast": contrast,
                "image_type": image_type,
                "processed_at": datetime.now().isoformat(),
                "description": self._generate_description(width, height, format_type, aspect_ratio, image_type, brightness)
            }
        except Exception as e:
            print(f"Error processing image: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "description": "Unable to process image"
            }
    
    def _get_dominant_colors(self, image, k=3):
        """Extract dominant colors from image"""
        try:
            # Resize for faster processing
            image.thumbnail((150, 150))
            pixels = list(image.getdata())
            
            # Simple color clustering - get most common colors
            color_counts = {}
            for pixel in pixels[:1000]:  # Sample first 1000 pixels
                # Round to nearest 10 for clustering
                r, g, b = pixel[:3]
                color_key = (r // 20 * 20, g // 20 * 20, b // 20 * 20)
                color_counts[color_key] = color_counts.get(color_key, 0) + 1
            
            # Get top colors
            top_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:k]
            return [f"rgb({r},{g},{b})" for (r, g, b), _ in top_colors]
        except:
            return ["rgb(128,128,128)"]
    
    def _get_brightness(self, image):
        """Calculate average brightness (0-255)"""
        try:
            pixels = list(image.getdata())
            brightness_values = [sum(pixel[:3]) / 3 for pixel in pixels[:1000]]
            avg_brightness = sum(brightness_values) / len(brightness_values)
            return round(avg_brightness, 1)
        except:
            return 128
    
    def _get_contrast(self, image):
        """Estimate contrast level"""
        try:
            # Convert to grayscale for contrast calculation
            gray = image.convert('L')
            pixels = list(gray.getdata())[:1000]
            
            if len(pixels) < 2:
                return "medium"
            
            min_val = min(pixels)
            max_val = max(pixels)
            contrast_range = max_val - min_val
            
            if contrast_range < 50:
                return "low"
            elif contrast_range < 150:
                return "medium"
            else:
                return "high"
        except:
            return "medium"
    
    def _detect_image_type(self, image, width, height):
        """Detect if image is likely a photo, diagram, screenshot, etc."""
        aspect = width / height if height > 0 else 1
        
        # Screenshots often have specific aspect ratios
        if abs(aspect - 16/9) < 0.1 or abs(aspect - 4/3) < 0.1:
            if width > 800:
                return "possibly_screenshot"
        
        # Very square images might be icons/logos
        if 0.9 < aspect < 1.1 and width < 500:
            return "possibly_icon"
        
        # Portrait/landscape detection
        if aspect > 1.5:
            return "landscape"
        elif aspect < 0.67:
            return "portrait"
        
        return "standard"
    
    def _generate_description(self, width, height, format_type, aspect_ratio, image_type, brightness):
        """Generate detailed image description"""
        desc = f"Image ({width}×{height}px, {format_type})"
        
        # Add orientation
        if aspect_ratio > 1.3:
            desc += " in landscape orientation"
        elif aspect_ratio < 0.77:
            desc += " in portrait orientation"
        else:
            desc += " in square/near-square orientation"
        
        # Add brightness info
        if brightness < 100:
            desc += ", appears dark"
        elif brightness > 200:
            desc += ", appears bright"
        
        # Add type hint
        if image_type == "possibly_screenshot":
            desc += ", may be a screenshot"
        elif image_type == "possibly_icon":
            desc += ", may be an icon or logo"
        
        return desc
    
    def describe_image(self, image_info):
        """Generate description of image"""
        if "error" in image_info:
            return "I couldn't process this image. Please try another format."
        
        return image_info.get('description', f"Image: {image_info.get('width', '?')}x{image_info.get('height', '?')} {image_info.get('format', 'unknown')} image")
    
    def enhance_image(self, image_data, enhancement_type="sharpness"):
        """Apply image enhancements"""
        try:
            # Decode image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            if enhancement_type == "sharpness":
                enhancer = ImageEnhance.Sharpness(image)
                enhanced = enhancer.enhance(1.5)
            elif enhancement_type == "contrast":
                enhancer = ImageEnhance.Contrast(image)
                enhanced = enhancer.enhance(1.2)
            elif enhancement_type == "brightness":
                enhancer = ImageEnhance.Brightness(image)
                enhanced = enhancer.enhance(1.1)
            else:
                enhanced = image
            
            # Convert to base64
            buffer = io.BytesIO()
            enhanced.save(buffer, format=image.format or 'PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/{image.format.lower() or 'png'};base64,{img_str}"
        except Exception as e:
            print(f"Error enhancing image: {e}")
            return None


# Global instance
_image_processor = None

def get_image_processor():
    """Get or create global image processor"""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor


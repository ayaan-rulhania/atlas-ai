"""
Image Handler - Provides reliable image fetching for Atlas AI.
Uses multiple fallback sources to ensure images always load.
"""

import re
import hashlib
import requests
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import quote_plus

from .trainx_image_map import TRAINX_IMAGE_MAP, TRAINX_ALIASES, resolve_subject_alias


class ImageHandler:
    """
    Handles image fetching from multiple sources with fallbacks.
    Replaces Unsplash with more reliable alternatives.
    """
    
    # Image source priority (most reliable first)
    IMAGE_SOURCES = [
        'pexels',
        'loremflickr',
        'picsum',
        'placeholder',
    ]
    
    # Basic safety filter for inappropriate subjects
    BANNED_SUBJECT_KEYWORDS = {
        "nsfw", "porn", "nude", "nudity", "sex", "sexual", "explicit",
        "gore", "violence", "bloody", "beheading", "decapitation",
        "self-harm", "suicide", "kill myself", "murder", "child sexual",
        "csam", "abuse", "torture", "rape"
    }
    
    def __init__(self, pexels_api_key: Optional[str] = None):
        """
        Initialize the image handler.
        
        Args:
            pexels_api_key: Optional Pexels API key for higher quality images
        """
        self.pexels_api_key = pexels_api_key
        self._cache: Dict[str, str] = {}
    
    def get_image(self, subject: str, size: str = "800x600", variant: Optional[str] = None) -> Tuple[str, str]:
        """
        Get a reliable image URL for the given subject.
        
        Args:
            subject: The image subject/search term
            size: Desired image size (widthxheight)
            
        Args:
            variant: Optional variant key to force a different result even for the same subject.

        Returns:
            Tuple of (url, source) where source is one of:
            'trainx', 'pexels', 'picsum', 'loremflickr', 'placeholder'
        """
        if not subject:
            return self._get_placeholder(size, "No subject"), "placeholder"
        
        subject = subject.strip()
        
        # Safety: block inappropriate subjects early
        if self._is_inappropriate_subject(subject):
            return self._get_placeholder(size, "Safe image"), "blocked"
        
        canonical = resolve_subject_alias(subject)
        
        # TrainX hardcoded mapping first
        if canonical in TRAINX_IMAGE_MAP:
            url = TRAINX_IMAGE_MAP[canonical]
            if self._validate_url(url):
                return url, "trainx"
        
        # Check cache (variant-aware so "another angle" actually changes)
        variant_key = (variant or "").strip()
        cache_key = f"{canonical}:{size}:{variant_key}"
        if cache_key in self._cache:
            return self._cache[cache_key], "cache"
        
        # Try sources in order (Pexels if key, then LoremFlickr seeded, then Picsum)
        for source in self.IMAGE_SOURCES:
            try:
                url = self._get_from_source(source, canonical, size, variant_key=variant_key)
                if url and self._validate_url(url):
                    self._cache[cache_key] = url
                    return url, source
            except Exception as e:
                print(f"[ImageHandler] {source} failed for '{canonical}': {e}")
                continue
        
        # Ultimate fallback
        return self._get_placeholder(size, canonical), "placeholder"
    
    def _get_from_source(self, source: str, subject: str, size: str, variant_key: str = "") -> str:
        """Get image from a specific source."""
        width, height = self._parse_size(size)
        
        if source == 'pexels' and self.pexels_api_key:
            return self._fetch_pexels(subject, width, height, variant_key=variant_key)
        elif source == 'picsum':
            return self._get_picsum(subject, width, height, variant_key=variant_key)
        elif source == 'loremflickr':
            return self._get_loremflickr(subject, width, height, variant_key=variant_key)
        elif source == 'placeholder':
            return self._get_placeholder(size, subject)
        
        return ""
    
    def _fetch_pexels(self, subject: str, width: int, height: int, variant_key: str = "") -> str:
        """Fetch image from Pexels API."""
        if not self.pexels_api_key:
            return ""
        
        headers = {"Authorization": self.pexels_api_key}
        # Pull more results and pick deterministically based on variant_key so "another" changes.
        url = f"https://api.pexels.com/v1/search?query={quote_plus(subject)}&per_page=15"
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            photos = data.get('photos') or []
            if photos:
                if variant_key:
                    idx = int(hashlib.md5(f"{subject}:{variant_key}".encode()).hexdigest()[:8], 16) % len(photos)
                else:
                    idx = 0
                photo = photos[idx]
                # Return the sized version
                src = photo.get('src', {})
                return src.get('large2x') or src.get('large') or src.get('medium', '')
        
        return ""
    
    def _get_picsum(self, subject: str, width: int, height: int, variant_key: str = "") -> str:
        """
        Get image from Lorem Picsum.
        Uses a deterministic seed based on subject for consistent images.
        """
        # Create a seed from (subject + variant) so the same prompt can produce different images.
        seed_input = f"{subject.lower()}::{variant_key}".encode()
        seed = hashlib.md5(seed_input).hexdigest()[:8]
        
        # Lorem Picsum provides beautiful placeholder images
        # The seed ensures the same subject always gets the same image
        return f"https://picsum.photos/seed/{seed}/{width}/{height}"

    def _get_loremflickr(self, subject: str, width: int, height: int, variant_key: str = "") -> str:
        """
        Get image from LoremFlickr with subject tags.
        """
        tag = quote_plus(subject)
        # `lock` forces a stable-but-different variant; changing it changes the returned image.
        lock = ""
        if variant_key:
            lock_num = int(hashlib.md5(f"{subject}:{variant_key}".encode()).hexdigest()[:6], 16) % 10000
            lock = f"?lock={lock_num}"
        return f"https://loremflickr.com/{width}/{height}/{tag}{lock}"
    
    def _get_placeholder(self, size: str, subject: str) -> str:
        """
        Get a placeholder image with the subject text.
        Uses placehold.co for reliable placeholder images.
        """
        width, height = self._parse_size(size)
        
        # URL-encode the subject for the placeholder text
        text = quote_plus(subject[:30]) if subject else "Image"
        
        # Use placehold.co - reliable placeholder service
        return f"https://placehold.co/{width}x{height}/5a5df0/ffffff?text={text}"
    
    def _parse_size(self, size: str) -> tuple:
        """Parse size string into width and height."""
        try:
            parts = size.lower().split('x')
            width = int(parts[0])
            height = int(parts[1]) if len(parts) > 1 else width
            return width, height
        except (ValueError, IndexError):
            return 800, 600
    
    def _is_inappropriate_subject(self, subject: str) -> bool:
        lowered = subject.lower()
        return any(keyword in lowered for keyword in self.BANNED_SUBJECT_KEYWORDS)
    
    def _validate_url(self, url: str) -> bool:
        """Validate that a URL is properly formatted."""
        if not url:
            return False
        return url.startswith('https://') and len(url) < 2000
    
    def format_image_response(self, subject: str, url: Optional[str] = None, is_trainx: bool = False) -> str:
        """
        Format a complete image response with markdown.
        
        Args:
            subject: The image subject
            url: Optional pre-fetched URL, will be fetched if not provided
            is_trainx: If True, also emit a TrainX iframe token for richer rendering
            
        Returns:
            Formatted markdown response with image
        """
        if not url:
            url, source = self.get_image(subject)
        else:
            source = "trainx" if is_trainx else "search"
        
        # Clean the subject for display
        display_subject = subject.strip().title()
        
        # If blocked, skip iframe and label clearly
        if source == "blocked":
            placeholder_url = url
            sections = [
                f"## Image request filtered",
                "This request matched our safety filters. Here's a safe placeholder instead.",
                f"![Safe Placeholder]({placeholder_url})",
                "**Source:** Safety filter"
            ]
            return "\n\n".join(sections)
        
        iframe_block = ""
        if is_trainx or source == "trainx":
            # Token consumed by frontend renderer to render iframe directly
            iframe_block = f"{{{{TRAINX_IFRAME:{url}}}}}\n\n"
        
        source_labels = {
            "trainx": "TrainX curated",
            "pexels": "Pexels",
            "picsum": "Picsum",
            "loremflickr": "LoremFlickr",
            "placeholder": "Placeholder"
        }
        source_label = source_labels.get(source, source.title())
        
        hero_media = f"{iframe_block}![{display_subject}]({url})".strip()
        
        sections = [
            f"## Image: {display_subject}",
            hero_media,
            f"**Source:** {source_label}",
            "### Next steps",
            "- Say **“another angle”** / **“another style”** / **“different background”** to fetch a new variant",
            "- Say **“bigger 1024x768”** (or any WxH) to change the size",
            "- Say **“change it to <new subject>”** to switch the subject"
        ]
        
        # Join non-empty sections with spacing to encourage rich formatting
        return "\n\n".join([section for section in sections if section])
    
    def extract_image_request(self, message: str) -> str:
        """
        Extract the subject of an image request from a message.
        
        Args:
            message: User message
            
        Returns:
            The image subject, or empty string if not an image request
        """
        if not message:
            return ""
        
        text = message.strip()
        patterns = [
            r'^\s*(?:create|generate|make|draw|show|find|get)\s+(?:me\s+)?(?:a\s+)?(?:beautiful\s+|personalized\s+|custom\s+|nice\s+|cool\s+)?(?:image|picture|photo|portrait|drawing|pic)\s+of\s+(.+)',
            r'\b(?:image|picture|photo|portrait|drawing|pic)\s+of\s+(.+)',
            r'^\s*(?:show|find|get)\s+(?:me\s+)?(?:a\s+)?(.+?)(?:\s+image|\s+picture|\s+photo)?\s*$',
        ]
        
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                subject = m.group(1).strip(" .!?")
                # Filter out non-image requests
                if subject and len(subject) < 100:
                    return subject
        
        return ""


# Singleton instance
_handler_instance = None


def get_image_handler(pexels_api_key: Optional[str] = None) -> ImageHandler:
    """Get the singleton ImageHandler instance."""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = ImageHandler(pexels_api_key)
    return _handler_instance

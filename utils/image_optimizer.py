"""Image optimization utility for ConnectSphere.

Resizes oversized images, compresses JPEG quality, and converts PNGs to WebP
where supported. Called on save hooks for posts, profiles, stories, and reels.
"""

import io
import os
from PIL import Image
from django.core.files.base import ContentFile


MAX_WIDTH = 1920
MAX_HEIGHT = 1920
JPEG_QUALITY = 82
WEBP_QUALITY = 80


def optimize_image(image_field, max_width=MAX_WIDTH, max_height=MAX_HEIGHT):
    """Optimize an ImageField in-place.

    - Resizes if any dimension exceeds max_width/max_height
    - Converts PNG → WebP
    - Compresses JPEG to JPEG_QUALITY
    - Returns True if the image was modified, False otherwise
    """
    if not image_field or not image_field.name:
        return False

    try:
        image_field.open()
        img = Image.open(image_field)
    except Exception:
        return False

    original_format = img.format or 'JPEG'
    modified = False

    # Convert RGBA to RGB for JPEG output
    if img.mode in ('RGBA', 'P'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        bg.paste(img, mask=img.split()[3])
        img = bg
        modified = True
    elif img.mode != 'RGB':
        img = img.convert('RGB')
        modified = True

    # Resize if too large
    width, height = img.size
    if width > max_width or height > max_height:
        img.thumbnail((max_width, max_height), Image.LANCZOS)
        modified = True

    # Choose output format
    name_base, ext = os.path.splitext(image_field.name)
    ext = ext.lower()

    if ext == '.png':
        # Convert PNG to WebP
        output_format = 'WEBP'
        quality = WEBP_QUALITY
        new_name = name_base + '.webp'
        modified = True
    elif ext in ('.webp',):
        output_format = 'WEBP'
        quality = WEBP_QUALITY
        new_name = image_field.name
        modified = True
    else:
        # Default to JPEG
        output_format = 'JPEG'
        quality = JPEG_QUALITY
        new_name = name_base + '.jpg' if ext not in ('.jpg', '.jpeg') else image_field.name
        modified = True

    if not modified:
        return False

    # Save to buffer
    buffer = io.BytesIO()
    save_kwargs = {'format': output_format, 'quality': quality, 'optimize': True}
    if output_format == 'JPEG':
        save_kwargs['progressive'] = True
    img.save(buffer, **save_kwargs)
    buffer.seek(0)

    # Replace the file content
    image_field.save(
        os.path.basename(new_name),
        ContentFile(buffer.read()),
        save=False,
    )

    return True


def get_image_dimensions(image_field):
    """Return (width, height) tuple for an image field."""
    try:
        image_field.open()
        img = Image.open(image_field)
        return img.size
    except Exception:
        return (0, 0)

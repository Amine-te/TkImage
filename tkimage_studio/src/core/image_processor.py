from __future__ import annotations

from typing import Tuple

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def resize_image(image: Image.Image, width: int, height: int) -> Image.Image:
    """Return a resized copy of the image."""
    return image.resize((int(width), int(height)), Image.LANCZOS)


def crop_image(image: Image.Image, box: Tuple[int, int, int, int]) -> Image.Image:
    """Return a cropped copy of the image using the given bounding box."""
    return image.crop(box)


def rotate_image(image: Image.Image, angle: float) -> Image.Image:
    """Return a rotated copy of the image."""
    return image.rotate(angle, expand=True)


def apply_grayscale(image: Image.Image) -> Image.Image:
    """Convert image to grayscale."""
    return image.convert("L").convert("RGB")


def apply_blur(image: Image.Image) -> Image.Image:
    """Apply a Gaussian blur."""
    return image.filter(ImageFilter.GaussianBlur(radius=2.0))


def apply_contrast(image: Image.Image, factor: float) -> Image.Image:
    """Adjust contrast using ImageEnhance.Contrast."""
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(float(factor))


def apply_brightness(image: Image.Image, factor: float) -> Image.Image:
    """Adjust brightness using ImageEnhance.Brightness."""
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(float(factor))


def apply_sharpness(image: Image.Image, factor: float) -> Image.Image:
    """Adjust sharpness using ImageEnhance.Sharpness."""
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(float(factor))


def apply_inversion(image: Image.Image) -> Image.Image:
    """Invert image colors."""
    # Ensure we are in RGB mode for inversion.
    rgb = image.convert("RGB")
    return ImageOps.invert(rgb)


def apply_autocontrast(image: Image.Image) -> Image.Image:
    """Apply automatic contrast correction."""
    return ImageOps.autocontrast(image)


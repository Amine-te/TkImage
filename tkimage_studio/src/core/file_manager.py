from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from PIL import Image


SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_IMAGES_DIR = BASE_DIR / "data" / "output_images"
OUTPUT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def open_image(path: str | Path) -> Image.Image:
    """
    Open an image from disk and return a PIL Image.

    The caller should wrap this in try/except and show any GUI errors.
    """
    p = Path(path)
    return Image.open(p).convert("RGB")


def open_folder(path: str | Path) -> List[Path]:
    """
    Return a list of image file paths from the given folder.

    Only files with supported extensions are included.
    """
    folder = Path(path)
    if not folder.is_dir():
        return []

    def is_image_file(p: Path) -> bool:
        return p.suffix.lower() in SUPPORTED_EXTENSIONS and p.is_file()

    files: Iterable[Path] = sorted(folder.iterdir())
    return [p for p in files if is_image_file(p)]


def save_image(image: Image.Image, path: str | Path) -> Path:
    """
    Save the given PIL image to disk at the provided path.

    The caller is responsible for handling any exceptions and for choosing
    a valid extension compatible with Pillow (e.g. .png, .jpg).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    image.save(p)
    return p


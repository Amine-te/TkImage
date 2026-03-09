from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import Image

from .file_manager import open_image


def load_image(path: str | Path) -> Optional[Image.Image]:
    """
    Load an image from disk and return a PIL Image, or None if loading fails.
    """
    try:
        return open_image(path)
    except Exception:
        # The caller is responsible for reporting detailed errors to the user.
        return None


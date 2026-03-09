from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional

from PIL import Image, ImageStat

from . import annotation_manager


def compute_stats(
    image: Image.Image,
    image_path: Optional[Path] = None,
    folder_images: Optional[Iterable[Path]] = None,
) -> Dict[str, Any]:
    """
    Compute statistics about the current image and (optionally) its dataset.

    Returns a dictionary with:
      - width, height, mode, file_size_kb
      - per-channel stats: mean, min, max
      - dataset_size (number of images in current folder)
      - images_per_class (mapping class -> count, from annotations)
      - average_note (float, across annotated images)
    """
    w, h = image.size
    mode = image.mode

    file_size_kb = 0.0
    if image_path is not None:
        try:
            file_size_kb = image_path.stat().st_size / 1024.0
        except OSError:
            file_size_kb = 0.0

    # Per-channel statistics using ImageStat.
    stat = ImageStat.Stat(image)
    means = stat.mean
    mins = stat.extrema

    # Normalize channel labels depending on mode.
    channel_labels: List[str]
    if mode == "L":
        channel_labels = ["L"]
    elif mode in ("RGB", "RGBA"):
        channel_labels = list(mode)
    else:
        # Generic fallback: label channels as C0, C1, ...
        channel_labels = [f"C{i}" for i in range(len(means))]

    channel_stats: Dict[str, Dict[str, float]] = {}
    for i, label in enumerate(channel_labels):
        ch_min, ch_max = mins[i]
        channel_stats[label] = {
            "mean": float(means[i]),
            "min": float(ch_min),
            "max": float(ch_max),
        }

    # Dataset-level statistics from annotations.
    dataset_size = len(list(folder_images)) if folder_images is not None else 0

    anns = annotation_manager.load_all_annotations()
    # If folder_images is provided, filter annotations to that set of filenames.
    if folder_images is not None:
        names = {p.name for p in folder_images}
        anns = [a for a in anns if a.filename in names]

    images_per_class: Dict[str, int] = Counter(
        a.classe for a in anns if a.classe
    )

    notes = [a.note for a in anns if a.note]
    average_note = float(sum(notes) / len(notes)) if notes else 0.0

    return {
        "width": w,
        "height": h,
        "mode": mode,
        "file_size_kb": file_size_kb,
        "channels": channel_stats,
        "dataset_size": dataset_size,
        "images_per_class": dict(images_per_class),
        "average_note": average_note,
    }


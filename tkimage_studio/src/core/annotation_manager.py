from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any, Iterable, List

import csv
import json


BASE_DIR = Path(__file__).resolve().parents[2]
ANNOTATIONS_DIR = BASE_DIR / "data" / "annotations"
ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Annotation:
    """Metadata associated with a single image for classification."""

    filename: str
    description: str = ""
    note: int = 0
    classe: str = ""
    tags: str = ""
    width: int = 0
    height: int = 0
    mode: str = ""
    file_size_kb: float = 0.0


def _annotation_path(image_path: Path) -> Path:
    """Return the JSON path used to store the annotation for an image."""
    return ANNOTATIONS_DIR / f"{image_path.stem}.json"


def save_annotation(
    image_path: Path,
    description: str,
    note: int,
    classe: str,
    tags: str,
    width: int,
    height: int,
    mode: str,
    file_size_kb: float,
) -> Path:
    """
    Save a single image annotation to disk as JSON.

    The annotation is stored at `data/annotations/{image_name}.json`.
    """
    ann = Annotation(
        filename=image_path.name,
        description=description,
        note=int(note),
        classe=classe,
        tags=tags,
        width=int(width),
        height=int(height),
        mode=mode,
        file_size_kb=float(file_size_kb),
    )
    path = _annotation_path(image_path)
    path.write_text(
        json.dumps(asdict(ann), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_annotation(image_path: Path) -> Optional[Annotation]:
    """
    Load an annotation for the given image path, if it exists.

    Returns an Annotation instance or None.
    """
    path = _annotation_path(image_path)
    if not path.exists():
        return None

    try:
        raw: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    return Annotation(
        filename=raw.get("filename", image_path.name),
        description=raw.get("description", ""),
        note=int(raw.get("note", 0) or 0),
        classe=raw.get("classe", ""),
        tags=raw.get("tags", ""),
        width=int(raw.get("width", 0) or 0),
        height=int(raw.get("height", 0) or 0),
        mode=raw.get("mode", ""),
        file_size_kb=float(raw.get("file_size_kb", 0.0) or 0.0),
    )


def _iter_annotation_files() -> Iterable[Path]:
    return sorted(ANNOTATIONS_DIR.glob("*.json"))


def load_all_annotations() -> List[Annotation]:
    """Return all annotations currently stored on disk."""
    anns: List[Annotation] = []
    for path in _iter_annotation_files():
        try:
            raw: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            anns.append(
                Annotation(
                    filename=raw.get("filename", path.stem),
                    description=raw.get("description", ""),
                    note=int(raw.get("note", 0) or 0),
                    classe=raw.get("classe", ""),
                    tags=raw.get("tags", ""),
                    width=int(raw.get("width", 0) or 0),
                    height=int(raw.get("height", 0) or 0),
                    mode=raw.get("mode", ""),
                    file_size_kb=float(raw.get("file_size_kb", 0.0) or 0.0),
                )
            )
        except Exception:
            continue
    return anns


def export_annotations_json(output_path: Optional[Path] = None) -> Path:
    """
    Export all annotations as a JSON list.

    Format: list of objects
      {filename, description, note, classe, tags, width, height, mode, file_size_kb}
    """
    anns = load_all_annotations()
    if output_path is None:
        output_path = ANNOTATIONS_DIR / "export.json"
    data = [asdict(a) for a in anns]
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


def export_annotations_csv(output_path: Optional[Path] = None) -> Path:
    """
    Export all annotations as CSV with columns:
    filename, description, note, classe, tags, width, height, mode, file_size_kb
    """
    anns = load_all_annotations()
    if output_path is None:
        output_path = ANNOTATIONS_DIR / "export.csv"

    fieldnames = [
        "filename",
        "description",
        "note",
        "classe",
        "tags",
        "width",
        "height",
        "mode",
        "file_size_kb",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ann in anns:
            writer.writerow(asdict(ann))
    return output_path


def import_annotations_json(input_path: Path) -> int:
    """
    Import annotations from an exported JSON file.

    Existing per-image JSON files will be overwritten for matching filenames.
    Returns the number of annotations imported.
    """
    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception:
        return 0

    if not isinstance(raw, list):
        return 0

    count = 0
    for item in raw:
        try:
            filename = item.get("filename")
            if not filename:
                continue
            # Reconstruct a pseudo image_path using filename; directory is irrelevant.
            image_path = Path(filename)
            save_annotation(
                image_path=image_path,
                description=item.get("description", ""),
                note=int(item.get("note", 0) or 0),
                classe=item.get("classe", ""),
                tags=item.get("tags", ""),
                width=int(item.get("width", 0) or 0),
                height=int(item.get("height", 0) or 0),
                mode=item.get("mode", ""),
                file_size_kb=float(item.get("file_size_kb", 0.0) or 0.0),
            )
            count += 1
        except Exception:
            continue
    return count



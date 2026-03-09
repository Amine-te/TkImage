from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image

from . import annotation_manager


try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
    import torchvision.transforms as T
except ImportError as exc:  # pragma: no cover - optional dependency
    torch = None
    nn = None
    DataLoader = None
    Dataset = object  # type: ignore
    T = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


@dataclass
class TrainingConfig:
    image_paths: List[Path]
    model_name: str = "simple_cnn"
    num_epochs: int = 5
    batch_size: int = 8
    learning_rate: float = 1e-3
    image_size: int = 128
    device: str = "cpu"


class AnnotationDataset(Dataset):  # type: ignore[misc]
    """Torch dataset backed by annotation JSON and in-memory list of image paths."""

    def __init__(self, image_paths: List[Path], image_size: int) -> None:
        if torch is None or T is None:
            raise RuntimeError(
                "PyTorch and torchvision are required for training. "
                "Install with: pip install torch torchvision",
            )

        self.image_paths = image_paths
        self.transform = T.Compose(
            [
                T.Resize((image_size, image_size)),
                T.ToTensor(),
            ]
        )

        anns = annotation_manager.load_all_annotations()
        # Build label mapping from classes present in annotations,
        # restricted to the set of filenames in image_paths.
        allowed_filenames = {p.name for p in image_paths}
        anns = [a for a in anns if a.filename in allowed_filenames and a.classe]
        classes = sorted({a.classe for a in anns})
        self.class_to_idx: Dict[str, int] = {c: i for i, c in enumerate(classes)}
        self.idx_to_class: Dict[int, str] = {i: c for c, i in self.class_to_idx.items()}

        self.samples: List[Tuple[Path, int]] = []
        for ann in anns:
            if ann.classe not in self.class_to_idx:
                continue
            # Find matching path from provided image_paths.
            matching = [p for p in image_paths if p.name == ann.filename]
            if not matching:
                continue
            img_path = matching[0]
            label = self.class_to_idx[ann.classe]
            self.samples.append((img_path, label))

        if not self.samples:
            raise RuntimeError(
                "Aucun échantillon valide trouvé. "
                "Assurez-vous que les annotations contiennent des classes "
                "et que les fichiers image existent dans le dossier choisi.",
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        x = self.transform(img)
        y = torch.tensor(label, dtype=torch.long)
        return x, y


def _build_model(model_name: str, num_classes: int) -> nn.Module:
    if nn is None:
        raise RuntimeError(
            "PyTorch is required for training. "
            "Install with: pip install torch torchvision",
        )

    if model_name == "simple_cnn":
        return nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(32 * 32 * 32, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes),
        )

    raise ValueError(f"Unknown model name: {model_name}")


def available_models() -> List[str]:
    """Return a list of supported model identifiers."""
    return ["simple_cnn"]


def train_model(
    config: TrainingConfig,
    log_fn: Optional[Callable[[str], None]] = None,
) -> Tuple[object, Dict[str, float]]:
    """
    Train a simple CNN classifier based on annotations.

    Returns a tuple (model, metrics) where metrics currently contains:
      - 'train_loss'
      - 'train_accuracy'
    """
    if torch is None or DataLoader is None:
        raise RuntimeError(
            "PyTorch is required for training. "
            "Install with: pip install torch torchvision",
        )

    def log(msg: str) -> None:
        if log_fn is not None:
            log_fn(msg)

    dataset = AnnotationDataset(config.image_paths, config.image_size)
    num_classes = len(dataset.class_to_idx)
    log(f"Classes ({num_classes}): {dataset.class_to_idx}")
    loader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True)

    device = torch.device(config.device if torch.cuda.is_available() else "cpu")
    model = _build_model(config.model_name, num_classes=num_classes).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)

    model.train()
    for epoch in range(1, config.num_epochs + 1):
        epoch_loss = 0.0
        correct = 0
        total = 0
        for inputs, targets in loader:
            inputs = inputs.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * inputs.size(0)
            _, preds = outputs.max(1)
            correct += preds.eq(targets).sum().item()
            total += targets.size(0)

        avg_loss = epoch_loss / max(1, total)
        acc = correct / max(1, total)
        log(f"Époque {epoch}/{config.num_epochs} — Perte: {avg_loss:.4f}, Précision: {acc:.3f}")

    metrics = {
        "train_loss": float(avg_loss),
        "train_accuracy": float(acc),
    }
    # Attach metadata for inference (class mapping).
    model.eval()
    model.class_to_idx = dataset.class_to_idx  # type: ignore[attr-defined]
    model.idx_to_class = dataset.idx_to_class  # type: ignore[attr-defined]
    model.image_size = config.image_size  # type: ignore[attr-defined]
    return model, metrics


def predict_single(
    model: object,
    image_path: Path,
) -> Tuple[str, List[Tuple[str, float]]]:
    """
    Run inference on a single image and return:
      - predicted class label
      - list of (class, probability) sorted by probability desc
    """
    if torch is None or T is None:
        raise RuntimeError(
            "PyTorch is required for inference. "
            "Install with: pip install torch torchvision",
        )

    m = model  # type: ignore[assignment]
    class_to_idx: Dict[str, int] = getattr(m, "class_to_idx")
    idx_to_class: Dict[int, str] = getattr(m, "idx_to_class")
    image_size: int = getattr(m, "image_size", 128)

    transform = T.Compose(
        [
            T.Resize((image_size, image_size)),
            T.ToTensor(),
        ]
    )
    img = Image.open(image_path).convert("RGB")
    x = transform(img).unsqueeze(0)

    device = next(m.parameters()).device  # type: ignore[arg-type]
    x = x.to(device)
    with torch.no_grad():
        outputs = m(x)
        probs = torch.softmax(outputs, dim=1)[0]

    topk = min(5, probs.size(0))
    prob_vals, idxs = probs.topk(topk)
    results: List[Tuple[str, float]] = []
    for i in range(topk):
        idx = int(idxs[i].item())
        cls = idx_to_class.get(idx, str(idx))
        p = float(prob_vals[i].item())
        results.append((cls, p))

    predicted_class = results[0][0] if results else ""
    return predicted_class, results


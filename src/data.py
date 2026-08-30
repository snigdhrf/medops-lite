"""Dataset loading and deterministic image preprocessing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image


IMAGE_SIZE = 28


def load_dataset(split: str, root: str = "data", download: bool = True) -> Any:
    """Load PneumoniaMNIST through the official MedMNIST dataset wrapper."""
    from medmnist import PneumoniaMNIST

    Path(root).mkdir(parents=True, exist_ok=True)
    return PneumoniaMNIST(
        split=split,
        root=root,
        download=download,
        transform=image_to_tensor,
        target_transform=_label_to_tensor,
    )


def image_to_tensor(image: Image.Image) -> torch.Tensor:
    """Convert an image to the model's normalized CHW tensor."""
    resized = image.convert("L").resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.BILINEAR)
    tensor = torch.from_numpy(np.asarray(resized, dtype=np.float32) / 255.0).unsqueeze(0)
    return (tensor - 0.5) / 0.5


def _label_to_tensor(label: object) -> torch.Tensor:
    target = int(np.asarray(label).reshape(-1)[0])
    if target not in (0, 1):
        raise ValueError(f"unexpected binary label: {target}")
    return torch.tensor(target, dtype=torch.long)

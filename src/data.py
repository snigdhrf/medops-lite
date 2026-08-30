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
    return PneumoniaMNIST(split=split, root=root, download=download)


def image_to_tensor(image: Image.Image) -> torch.Tensor:
    """Convert an image to the model's normalized CHW tensor."""
    resized = image.convert("L").resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.BILINEAR)
    tensor = torch.from_numpy(np.asarray(resized, dtype=np.float32) / 255.0).unsqueeze(0)
    return (tensor - 0.5) / 0.5


class PreparedDataset(torch.utils.data.Dataset):
    """Adapter that makes MedMNIST samples explicit and testable."""

    def __init__(self, dataset: Any) -> None:
        self.dataset = dataset

    def __len__(self) -> int:
        return len(self.dataset)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        image, label = self.dataset[index]
        target = int(np.asarray(label).reshape(-1)[0])
        if target not in (0, 1):
            raise ValueError(f"unexpected binary label: {target}")
        return image_to_tensor(image), torch.tensor(target, dtype=torch.long)


def ensure_directory(path: str) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

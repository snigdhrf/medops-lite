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

    if split not in {"train", "val", "test"}:
        raise ValueError("split must be train, val, or test")
    Path(root).mkdir(parents=True, exist_ok=True)
    return PneumoniaMNIST(split=split, root=root, download=download)


def image_to_tensor(image: Any) -> torch.Tensor:
    """Convert a grayscale image to the model's normalized CHW tensor."""
    if isinstance(image, torch.Tensor):
        tensor = image.detach().float()
        if tensor.ndim == 2:
            tensor = tensor.unsqueeze(0)
        if tensor.ndim != 3:
            raise ValueError("image tensor must have shape HxW or CxHxW")
        if tensor.shape[0] != 1:
            tensor = tensor[:1]
        if tensor.max() > 1:
            tensor = tensor / 255.0
    else:
        array = np.asarray(image)
        if array.ndim == 3:
            array = array[..., 0]
        if array.ndim != 2:
            raise ValueError("image must be a 2D grayscale image")
        pil_image = Image.fromarray(array.astype(np.uint8)).resize(
            (IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.BILINEAR
        )
        tensor = torch.from_numpy(np.asarray(pil_image, dtype=np.float32) / 255.0)
        tensor = tensor.unsqueeze(0)

    if tuple(tensor.shape[-2:]) != (IMAGE_SIZE, IMAGE_SIZE):
        tensor = torch.nn.functional.interpolate(
            tensor.unsqueeze(0), size=(IMAGE_SIZE, IMAGE_SIZE), mode="bilinear", align_corners=False
        ).squeeze(0)
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

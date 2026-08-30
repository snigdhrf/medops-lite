"""Train and evaluate the baseline model."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from .data import load_dataset
from .evaluate import evaluate
from .model import PneumoniaCNN


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def train(args: argparse.Namespace) -> dict[str, object]:
    seed_everything(args.seed)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    train_data = load_dataset("train", args.data_dir)
    val_data = load_dataset("val", args.data_dir)
    train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=args.batch_size)

    model = PneumoniaCNN()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    labels = torch.tensor([label.item() for _, label in train_data])
    class_counts = torch.bincount(labels, minlength=2).float()
    class_weights = class_counts.sum() / (2 * class_counts.clamp_min(1))
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)
    best_val_metrics: dict[str, float | list[list[int]]] | None = None
    best_state: dict[str, torch.Tensor] | None = None
    for _ in range(args.epochs):
        model.train()
        for images, labels in train_loader:
            optimizer.zero_grad()
            loss_fn(model(images), labels).backward()
            optimizer.step()
        current_val_metrics = evaluate(model, val_loader)
        if best_val_metrics is None or current_val_metrics["f1"] > best_val_metrics["f1"]:
            best_val_metrics = current_val_metrics
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    test_data = load_dataset("test", args.data_dir)
    metrics = evaluate(model, DataLoader(test_data, batch_size=args.batch_size))
    checkpoint = output / "model.pt"
    torch.save(model.state_dict(), checkpoint)
    metadata = {
        "seed": args.seed,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "class_weights": class_weights.tolist(),
        "git_commit": os.getenv("GIT_COMMIT", "unknown"),
        "validation_metrics": best_val_metrics,
        "metrics": metrics,
    }
    (output / "metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    import mlflow

    mlflow.set_tracking_uri(args.mlflow_uri)
    with mlflow.start_run():
        mlflow.log_params({key: metadata[key] for key in ("seed", "epochs", "batch_size", "learning_rate", "class_weights")})
        mlflow.log_metrics({key: value for key, value in metrics.items() if isinstance(value, float)})
        if best_val_metrics:
            mlflow.log_metrics({f"val_{key}": value for key, value in best_val_metrics.items() if isinstance(value, float)})
        mlflow.log_artifact(str(checkpoint))
        mlflow.log_artifact(str(output / "metrics.json"))
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output", default="artifacts")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mlflow-uri", default="sqlite:///mlflow.db")
    print(json.dumps(train(parser.parse_args()), indent=2))


if __name__ == "__main__":
    main()

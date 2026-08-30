"""Evaluation metrics with no dependency on a metrics framework."""

from __future__ import annotations

import time
from typing import Iterable

import torch


def evaluate(model: torch.nn.Module, batches: Iterable[tuple[torch.Tensor, torch.Tensor]]) -> dict[str, float | list[list[int]]]:
    model.eval()
    matrix = [[0, 0], [0, 0]]
    elapsed = 0.0
    examples = 0
    with torch.no_grad():
        for images, labels in batches:
            started = time.perf_counter()
            predictions = model(images).argmax(dim=1)
            elapsed += time.perf_counter() - started
            for actual, predicted in zip(labels.tolist(), predictions.tolist()):
                matrix[actual][predicted] += 1
            examples += len(labels)

    true_negative, false_positive = matrix[0]
    false_negative, true_positive = matrix[1]
    accuracy = (true_positive + true_negative) / max(examples, 1)
    precision = true_positive / max(true_positive + false_positive, 1)
    recall = true_positive / max(true_positive + false_negative, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "inference_ms_per_image": elapsed * 1000 / max(examples, 1),
        "confusion_matrix": matrix,
    }

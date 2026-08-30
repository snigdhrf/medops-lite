import numpy as np
import torch

from src.data import image_to_tensor
from src.evaluate import evaluate
from src.model import PneumoniaCNN


def test_preprocessing_is_deterministic_and_normalized():
    image = np.arange(64, dtype=np.uint8).reshape(8, 8)
    first = image_to_tensor(image)
    second = image_to_tensor(image)
    assert first.shape == (1, 28, 28)
    assert torch.equal(first, second)
    assert -1.0 <= float(first.min()) <= 1.0


def test_model_output_and_metrics_shape():
    model = PneumoniaCNN()
    output = model(torch.zeros(2, 1, 28, 28))
    assert output.shape == (2, 2)
    metrics = evaluate(model, [(torch.zeros(2, 1, 28, 28), torch.tensor([0, 1]))])
    assert set(("accuracy", "precision", "recall", "f1", "inference_ms_per_image")) <= metrics.keys()
    assert len(metrics["confusion_matrix"]) == 2

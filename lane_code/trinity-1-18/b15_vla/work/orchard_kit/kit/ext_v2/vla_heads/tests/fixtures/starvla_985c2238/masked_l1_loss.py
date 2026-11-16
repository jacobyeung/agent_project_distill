# Copied verbatim from StarVLA commit 985c2238 (vla_libero/work/src), starVLA/model/framework/VLM4A/QwenOFT.py lines 40-51,
# file sha256 b65da4bf86b9d6c571c7a3217307042cc884d1c655f91a0268cccaf1f6033f32. Used only by the loss-parity test.
import torch

def masked_l1_loss(prediction: torch.Tensor, target: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
    """Mean L1 over valid action cells, preserving legacy behavior without a mask."""
    error = torch.abs(prediction - target)
    if mask is None:
        return error.mean()
    valid = mask.to(device=error.device, dtype=error.dtype)
    if valid.shape != error.shape:
        raise ValueError(f"action_mask shape {tuple(valid.shape)} != action shape {tuple(error.shape)}")
    denominator = valid.sum()
    if not torch.any(mask):
        raise ValueError("action_mask contains no valid targets")
    return (error * valid).sum() / denominator

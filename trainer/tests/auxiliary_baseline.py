"""Frozen copies of the loss path before auxiliary heads (commit b4b2979).

The disabled-path test compares the current trainer against these bytes, so
the comparison needs neither Git nor a second checkout.
"""
from contextlib import nullcontext

import torch
import torch.nn.functional as F


def supervised_logits(model, batch, positions):
    """Project only supervised hidden states while preserving PEFT/DDP forward hooks."""
    targets = batch["labels"][:, positions + 1]
    rows, columns = torch.where(targets != -100)
    unwrapped = model.module if isinstance(model, torch.nn.parallel.DistributedDataParallel) else model
    head = unwrapped.get_output_embeddings()

    def select_hidden_states(module, args):
        hidden = args[0]
        if hidden.shape[:2] != targets.shape:
            raise ValueError("LM head hidden states do not align with selected causal positions")
        return (hidden[rows, columns], *args[1:])

    # Native Qwen forwards select the sequence positions before calling this head.
    # Pack the remaining batch dimension so mixed rows never project masked tokens.
    handle = head.register_forward_pre_hook(select_hidden_states, prepend=True)
    try:
        output = model(**{key: value for key, value in batch.items() if key != "labels"},
                       logits_to_keep=positions, use_cache=False, output_hidden_states=False, return_dict=True)
    finally:
        handle.remove()
    if output.logits.ndim != 2 or output.logits.shape[0] != rows.numel():
        raise ValueError("LM head must return exactly one logit vector per supervised token")
    return output.logits


def collate_rows(rows, pad_token_id):
    fields = {"input_ids", "attention_mask", "labels"}
    optional = {"mm_token_type_ids", "pixel_values_videos", "video_grid_thw"}
    if (not rows or any(not fields <= row.keys() or set(row) - fields - optional for row in rows)
            or any(set(row) != set(rows[0]) for row in rows)):
        raise ValueError("Micro-batches require matching, assistant-masked RGB tensor fields")
    if any(row["input_ids"].ndim != 2 or row["input_ids"].shape[0] != 1 for row in rows):
        raise ValueError("Collation accepts independently audited single-row encodings")
    length = max(row["input_ids"].shape[1] for row in rows)
    batch = {}
    for key in rows[0]:
        if key in fields or key == "mm_token_type_ids":
            if any(row[key].shape != row["input_ids"].shape for row in rows):
                raise ValueError("Token tensors changed shape during collation")
            fill = -100 if key == "labels" else pad_token_id if key == "input_ids" else 0
            batch[key] = torch.cat([F.pad(row[key], (0, length - row[key].shape[1]), value=fill) for row in rows])
        else:
            batch[key] = torch.cat([row[key] for row in rows])
    if torch.any(batch["labels"][batch["attention_mask"] == 0] != -100):
        raise ValueError("Padding tokens must never receive assistant supervision")
    return batch


def row_losses(model, batch):
    labels = batch["labels"]
    if labels.ndim != 2 or torch.any(labels[:, 0] != -100):
        raise ValueError("Every row must start with an unsupervised causal prompt")
    positions = torch.where((labels[:, 1:] != -100).any(dim=0))[0]
    targets = labels[:, positions + 1]
    counts = (targets != -100).sum(dim=1)
    if not positions.numel() or torch.any(counts == 0):
        raise ValueError("Every real or padding row requires a nonempty assistant target")
    supervised = targets != -100
    logits = supervised_logits(model, batch, positions)
    losses = F.cross_entropy(logits.float(), targets[supervised], reduction="none")
    row_indices = torch.where(supervised)[0]
    return losses.new_zeros(labels.shape[0]).index_add(0, row_indices, losses) / counts


def backward_batch(model, batch, weights, world_size, global_batch_size, synchronize=True, forward_context=None):
    context = model.no_sync() if not synchronize and hasattr(model, "no_sync") else nullcontext()
    with context:
        with forward_context if forward_context is not None else nullcontext():
            losses = row_losses(model, batch)
        weights = torch.as_tensor(weights, dtype=losses.dtype, device=losses.device)
        if weights.shape != losses.shape or not torch.all((weights == 0) | (weights == 1)):
            raise ValueError("Distributed row weights must be exact active/padding indicators")
        if not torch.isfinite(losses).all():
            raise ValueError("Nonfinite assistant-token loss")
        (losses.mul(weights).sum() * (world_size / global_batch_size)).backward()
    return losses.detach()

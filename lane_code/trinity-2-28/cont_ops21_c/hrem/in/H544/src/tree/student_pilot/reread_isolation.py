"""Shared isolation block extracted from hrp_infer's read_image().

The original block and its source hash are recorded in SOURCE_PINS.json.
The callback receives no main KV/GDN cache. It must use fresh image inputs.
"""

MAX_NEW_TOKENS = 48


def isolated(model, operation):
    from .mdg_lora import _MASK
    gate = _MASK.set(None)
    rope = model.model.rope_deltas
    try:
        model.model.rope_deltas = None
        return operation()
    finally:
        model.model.rope_deltas = rope
        _MASK.reset(gate)

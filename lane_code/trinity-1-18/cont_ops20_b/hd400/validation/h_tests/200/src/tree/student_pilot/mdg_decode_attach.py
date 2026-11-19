"""Attach a local MDG inference artifact before routed generate()."""
from pathlib import Path

from . import mdg_features, mdg_lora
from .mask_grounding_head import load_artifact


def attach_mdg(model, processor, directory, *, base_artifact_sha256=None):
    """Validate dimensions/base/tau and attach decoder plus optional span adapters.

    The decoder stays an auxiliary inference module on the LM's device. The
    caller owns the model's eval mode. No files are fetched or written.
    """
    if getattr(model, 'grounding_head', None) is not None:
        raise ValueError('Attach one grounding backend per decode')
    head, meta = load_artifact(Path(directory))
    cfg = head.cfg
    if (cfg.lm_dim != model.config.text_config.hidden_size
            or cfg.vit_dim != model.config.vision_config.hidden_size or cfg.geo_dim):
        raise ValueError('MDG artifact dimensions differ from decoder inputs')
    if base_artifact_sha256 is not None and meta['base_artifact']['sha256'] != base_artifact_sha256:
        raise ValueError('MDG artifact names another LM base')
    tau = meta.get('tau')
    if type(tau) not in (float, int) or not 0 <= tau <= 1:
        raise ValueError('MDG artifact requires frozen tau in [0,1]')
    mdg_features.bind_processor(model, processor)
    if (meta.get('lora_config') or {}).get('opener_tokens'):
        from . import ground_tokens
        fresh = any(o not in processor.tokenizer.get_vocab() for o in ground_tokens.OPENERS)
        ground_tokens.add(processor)
        if fresh:
            ground_tokens.initialize(model, processor)
        else:
            ground_tokens.bind(model, processor)
    if meta.get('lora_config'):
        mdg_lora.install(model, meta['lora_config']['rank'])
        mdg_lora.load(model, directory, meta)
    head.to(model.get_input_embeddings().weight.device).float().eval().requires_grad_(False)
    model.mdg_head, model.mdg_meta = head, meta
    mdg_features.bind_processor(model, processor)
    return meta

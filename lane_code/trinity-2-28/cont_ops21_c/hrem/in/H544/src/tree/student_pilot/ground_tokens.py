"""Deterministic atomic grounding opener for suffix-gated Stage-B decoding."""
OPENERS = ('<ground', '<gap')
OPENER = OPENERS[0]


def enabled(receipt):
    return bool(receipt.get('mdg'))


def add(processor):
    """Share decode's tokenizer binding and retain the two-row initialization pin."""
    from .mdg_decode_tokens import add_ground_tokens
    tokens = add_ground_tokens(processor)
    processor._ground_tokens = dict(ids={o: tokens['ids'][o] for o in OPENERS},
                                   constituents={o: tokens['constituents'][o] for o in OPENERS})
    return processor._ground_tokens


def initialize(model, processor):
    """Use the existing reserved embedding rows and constituent-mean initialization."""
    from .carrier_c1_routing import init_routing_embeddings
    tokens = processor._ground_tokens
    init_routing_embeddings(model, tokens)
    return bind(model, processor)


def bind(model, processor):
    """Bind token identities without overwriting a loaded export's learned rows."""
    tokens = processor._ground_tokens
    model.ground_token_ids = dict(tokens['ids'])
    model.ground_token_id = tokens['ids'][OPENER]
    return model.ground_token_id


def install_rows(model, ids=None):
    """Share two trainable rows between ordinary LM and MDG-query forwards."""
    import torch
    from torch import nn

    ids = dict(ids or model.ground_token_ids)
    if set(ids) != set(OPENERS) or any(type(i) is not int or i < 0 for i in ids.values()):
        raise ValueError('Stage-B opener rows require both atomic opener IDs')
    if hasattr(model, 'ground_token_ids') and ids != model.ground_token_ids:
        raise ValueError('Stage-B opener IDs differ from the processor')
    tokenizer = model.mdg_tokenizer
    if any(tokenizer.encode(text, add_special_tokens=False) != [index] for text, index in ids.items()):
        raise ValueError('Stage-B opener rows require the matching atomic tokenizer')
    if 'opener_rows' in model.auxiliary_heads.mdg_lora:
        if model.mdg_lora_config.get('opener_tokens') != ids:
            raise ValueError('Stage-B opener row contract differs')
        return
    embedding, head = model.get_input_embeddings(), model.get_output_embeddings()
    indices = [ids[text] for text in OPENERS]
    if max(indices) >= min(embedding.weight.shape[0], head.weight.shape[0]):
        raise ValueError('Stage-B opener rows exceed the reserved vocabulary')
    rows = nn.Module()
    rows.input_rows = nn.Parameter(embedding.weight[indices].detach().float().clone())
    rows.output_rows = nn.Parameter(head.weight[indices].detach().float().clone())
    warm = getattr(model, '_ground_warm_rows', None)
    if warm is not None:
        with torch.no_grad():
            for name in ('input_rows', 'output_rows'):
                parameter = getattr(rows, name)
                if warm[name].shape != parameter.shape:
                    raise ValueError('Warm-start opener row dimensions differ')
                parameter.copy_(warm[name].to(parameter))
    model.auxiliary_heads.mdg_lora['opener_rows'] = rows
    model.mdg_lora_config['opener_tokens'] = ids
    model.ground_token_ids = ids

    bind_rows(model, rows, indices)


def bind_rows(model, rows, indices=None):
    """Use one row owner in ordinary LM and isolated MDG-query forwards."""
    indices = indices or [model.ground_token_ids[text] for text in OPENERS]
    embedding, head = model.get_input_embeddings(), model.get_output_embeddings()
    embedding.__dict__['_mdg_opener_rows'] = rows
    embedding.__dict__['_mdg_opener_indices'] = indices
    head.__dict__['_mdg_opener_rows'] = rows
    head.__dict__['_mdg_opener_indices'] = indices
    embedding.register_forward_hook(_input_rows)
    head.register_forward_hook(_output_rows)


def _input_rows(module, args, output):
    tokens = args[0]
    result = output
    rows = module.__dict__['_mdg_opener_rows']
    for slot, index in enumerate(module.__dict__['_mdg_opener_indices']):
        selected = tokens == index
        if selected.any():
            if result is output:
                result = output.clone()
            result[selected] = rows.input_rows[slot].to(output.dtype)
    return result


def _output_rows(module, args, output):
    import torch
    from torch.nn import functional as F
    # Linear backward needs its input/weight, not the output. Replacing these
    # two columns in-place avoids another [tokens, vocabulary] allocation.
    result = output
    rows = module.__dict__['_mdg_opener_rows']
    with torch.autocast(device_type=output.device.type, enabled=False):
        logits = F.linear(args[0].float(), rows.output_rows).to(output.dtype)
    for slot, index in enumerate(module.__dict__['_mdg_opener_indices']):
        result[..., index] = logits[..., slot]
    return result


def materialize_export_rows(state, model):
    """Write the shared learned rows into the LM export as well as lora.pt."""
    import torch
    config = getattr(model, 'mdg_lora_config', {})
    ids = config.get('opener_tokens')
    if not ids:
        return state
    result = dict(state)
    indices = [ids[text] for text in OPENERS]
    for suffix, row_name in (('language_model.embed_tokens.weight', 'input_rows'),
                             ('lm_head.weight', 'output_rows')):
        keys = [key for key in state if key.endswith(suffix)]
        if len(keys) != 1:
            raise ValueError('Ambiguous opener-row LM export tensor')
        key = keys[0]
        rows = state['auxiliary_heads.mdg_lora.opener_rows.'+row_name]
        result[key] = state[key].clone()
        with torch.no_grad():
            result[key][indices] = rows.to(result[key])
    return result


def initialize_after_warm(model, processor, report=None):
    """Retain materialized opener rows when continuing an E2E LM artifact."""
    from .carrier_c1_routing import init_routing_embeddings
    saved = (report or {}).get('ground_token_ids')
    tokens = processor._routing_tokens
    if saved:
        if saved != processor._ground_tokens['ids']:
            raise ValueError('Warm-start grounding token IDs differ')
        tokens = {key: {text: value for text, value in items.items() if text not in OPENERS}
                  for key, items in tokens.items()}
    init_routing_embeddings(model, tokens)
    return bind(model, processor) if saved else initialize(model, processor)


def retain_warm_rows(model, heads, ids):
    """Keep authenticated FP32 row payloads across a BF16 LM warm start."""
    if hasattr(model, 'ground_token_ids') and model.ground_token_ids != ids:
        raise ValueError('Warm-start grounding token IDs differ')
    prefix = 'mdg_lora.opener_rows.'
    model._ground_warm_rows = {name: heads[prefix+name].detach().float().clone()
                              for name in ('input_rows', 'output_rows')}

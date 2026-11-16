"""Atomic grounding openers, using the existing routing-token mechanism."""
from transformers import AddedToken


OPENERS = ('<ground', '<gap')


def add_ground_tokens(processor, model=None):
    """Extend a processor with atomic openers and mean-initialized model rows.

    Call before creating training rows. Existing routing IDs and trained rows
    remain intact. TB-1 owns selective row training and artifact persistence.
    """
    tokenizer = processor.tokenizer
    tokens = getattr(processor, '_routing_tokens', None)
    if tokens is None:
        raise ValueError('Bind the existing routing tokens before ground/gap')
    existing = tokenizer.get_vocab()
    added = {}
    for opener in OPENERS:
        if opener in tokens['ids']:
            encoded = tokenizer.encode(opener, add_special_tokens=False)
            if encoded != [tokens['ids'][opener]]:
                raise ValueError('Grounding opener is not atomic')
            continue
        if opener in existing:
            raise ValueError('Unbound grounding opener already exists')
        added[opener] = tokenizer.encode(opener, add_special_tokens=False)
    if added:
        tokenizer.add_tokens([AddedToken(o, normalized=False, special=False) for o in added])
        fresh = dict(ids={o: tokenizer.convert_tokens_to_ids(o) for o in added}, constituents=added)
        if model is not None:
            from .carrier_c1_routing import init_routing_embeddings
            init_routing_embeddings(model, fresh)
        tokens['ids'].update(fresh['ids'])
        tokens['constituents'].update(added)
    return tokens

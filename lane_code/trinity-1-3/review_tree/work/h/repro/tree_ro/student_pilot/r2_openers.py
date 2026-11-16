"""Preserve trained opener rows only with an authenticated vocabulary witness."""
from .p3_provenance import digest, load, pinned
from .r2_contract import INIT


def vocabulary(processor):
    return dict(vocabulary_sha256=digest(processor.tokenizer.get_vocab()),
                tokens=processor._routing_tokens)


def initialize(model, processor, receipt):
    from . import carrier_c1_routing as routing
    policy = receipt.get('routing_opener_init', 'reset')
    if policy not in ('keep', 'reset'):
        raise ValueError('Unknown routing opener initialization')
    init = receipt.get('init_artifact') or {}
    report = getattr(model, 'init_report', {})
    warm = init.get('lm') == 'full' and report.get('lm_tensors', 0) > 0
    same = (init.get('artifact', {}).get('sha256') == INIT['artifact_sha256']
            or report.get('r2_lineage') == INIT['artifact_sha256'])
    if policy == 'keep' and warm and same:
        witness_pin = receipt.get('routing_vocabulary')
        if not witness_pin:
            raise ValueError('Missing routing vocabulary witness for keep warm start')
        witness = load(pinned(witness_pin))
        live = vocabulary(processor)
        if (witness.get('artifact_sha256') != init['artifact']['sha256']
                or witness.get('lineage_sha256') != INIT['artifact_sha256']
                or any(witness.get(k) != v for k, v in live.items())):
            raise ValueError('Routing opener lineage or vocabulary differs')
        model.routing_vocabulary = live
        return 'kept'
    routing.init_routing_embeddings(model, processor._routing_tokens)
    model.routing_vocabulary = vocabulary(processor)
    return 'reset'

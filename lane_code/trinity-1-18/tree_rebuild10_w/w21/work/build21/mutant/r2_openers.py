"""Preserve trained opener rows only with an authenticated vocabulary witness."""
from .p3_provenance import digest, load, pinned
from .r2_contract import bound_init


def vocabulary(processor):
    return dict(vocabulary_sha256=digest(processor.tokenizer.get_vocab()),
                tokens=processor._routing_tokens)


def policy(cfg):
    """A donor export keeps its trained rows across the R1 init boundary."""
    policy = cfg.get('routing_opener_init', 'reset')
    if policy not in ('keep', 'reset'):
        raise ValueError('Unknown routing opener initialization')
    if cfg.get('r1_training'):
        from .r1_training import PARENT
        artifact = (cfg.get('init_artifact') or {}).get('artifact', {})
        if artifact.get('sha256') != PARENT and policy != 'keep':
            raise ValueError('P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED:routing_opener_init')
    return policy


def preparation(cfg):
    selected = policy(cfg)
    if selected == 'reset':
        return
    init = cfg.get('init_artifact') or {}
    if init.get('lm') != 'full':
        raise ValueError('Keep requires a full warm start')
    if cfg.get('r1_training'):
        from .r1_training import start
        start(cfg)
    else:
        from .r2_contract import lineage_init
        lineage_init(init.get('artifact', {}), init=bound_init(cfg))
    witness_pin = cfg.get('routing_vocabulary')
    if not witness_pin:
        raise ValueError('Missing routing vocabulary witness for keep warm start')
    witness = load(pinned(witness_pin))
    if (witness.get('artifact_sha256') != init['artifact']['sha256']
            or witness.get('lineage_sha256') != bound_init(cfg)['artifact_sha256']
            or not witness.get('vocabulary_sha256') or not witness.get('tokens')):
        raise ValueError('Routing opener lineage or vocabulary differs')


def start_context(receipt):
    """Recover the full configuration carried by the authenticated prepared reader."""
    if receipt.get('schema') != 'c1-preparation-v1':
        return receipt
    cfg = receipt.get('_r1_start_config')
    if not isinstance(cfg, dict):
        raise ValueError('R1_OPENER_START_CONFIG_REQUIRED')
    from .carrier_c1_run import identity
    if (identity(cfg) != receipt.get('config_sha256')
            or any(cfg.get(k) != receipt.get(k) for k in ('r1_training','init_artifact','routing_opener_init','routing_vocabulary'))
            or cfg.get('streams') != {k:v['receipt'] for k,v in receipt.get('streams',{}).items()}):
        raise ValueError('R1_OPENER_START_CONFIG_MISMATCH')
    return cfg


def initialize(model, processor, receipt):
    from . import carrier_c1_routing as routing
    selected = policy(receipt)
    init = receipt.get('init_artifact') or {}
    report = getattr(model, 'init_report', {})
    warm = init.get('lm') == 'full' and report.get('lm_tensors', 0) > 0
    same = warm and selected == 'keep' and (init.get('artifact', {}).get('sha256') == bound_init(receipt)['artifact_sha256']
            or report.get('r2_lineage') == bound_init(receipt)['artifact_sha256'])
    if receipt.get('r1_training') and selected == 'keep':
        from .r1_training import start
        start(start_context(receipt))
        same = warm
    if selected == 'keep' and not (warm and same):
        raise ValueError('Keep requires a full warm start in the bound lineage')
    if selected == 'keep' and warm and same:
        witness_pin = receipt.get('routing_vocabulary')
        if not witness_pin:
            raise ValueError('Missing routing vocabulary witness for keep warm start')
        witness = load(pinned(witness_pin))
        live = vocabulary(processor)
        if (witness.get('artifact_sha256') != init['artifact']['sha256']
                or witness.get('lineage_sha256') != bound_init(receipt)['artifact_sha256']
                or any(witness.get(k) != v for k, v in live.items())):
            raise ValueError('Routing opener lineage or vocabulary differs')
        model.routing_vocabulary = live
        return 'kept'
    routing.init_routing_embeddings(model, processor._routing_tokens)
    model.routing_vocabulary = vocabulary(processor)
    return 'reset'

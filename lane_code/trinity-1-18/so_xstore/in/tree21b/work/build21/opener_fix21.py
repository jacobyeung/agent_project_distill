from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1'
def edit(name,old,new):
 p=T/name;text=p.read_text();assert old in text
 base=B/'base'/name;base.parent.mkdir(parents=True,exist_ok=True)
 if not base.exists():base.write_text(text)
 p.write_text(text.replace(old,new))
edit('student_pilot/carrier_c1_run.py','    return receipt, model\n\n\ndef load_model',
 '''    if cfg.get('r1_training'):
        receipt = {**receipt, '_r1_start_config': copy.deepcopy(cfg)}
    return receipt, model


def load_model''')
edit('student_pilot/r2_openers.py','def initialize(model, processor, receipt):',
 '''def start_context(receipt):
    """Recover the full configuration carried by the authenticated prepared reader."""
    from .r1_training import PARENT
    if (receipt.get('schema') != 'c1-preparation-v1'
            or (receipt.get('init_artifact') or {}).get('artifact',{}).get('sha256') == PARENT):
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


def initialize(model, processor, receipt):''')
edit('student_pilot/r2_openers.py','        start(receipt)','        start(start_context(receipt))')
print('Bound opener continuation to the authenticated full configuration')

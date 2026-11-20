"""Reconstruct P's pinned database using its authenticated native recipe."""
from pathlib import Path
from copy import deepcopy


def reconstruct(cfg, root):
    from z import load, checked, write
    from i import refresh
    from student_pilot.p3_provenance import pinned
    from student_pilot.s1_routing import build
    p = load(pinned(cfg['r1_training']['p_run']['config']))
    pin = p['streams']['routing']
    if pin['sha256'] != 'ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984':
        raise ValueError('P_TRAINED_ROUTING_PIN_DIFFERS')
    receipt = load(pinned(pin))
    expected = receipt['database']['sha256']
    if expected != '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84':
        raise ValueError('P_TRAINED_ROUTING_DATABASE_DIFFERS')
    recipe = load(pinned(receipt['materialization']))
    pcfg = deepcopy(p)
    pcfg['s1_routing'] = recipe['inputs']
    pcfg['streams']['routing'] = recipe['legacy']
    pin = write(Path(root)/'base_input.json',pcfg)
    request = refresh(dict(config=pin,staged_pins=[pin]),Path(root)/'base_refresh')
    rebuilt = build(load(pinned(request['config'])),Path(root)/'base',recipe['division'],recipe['base_model'])
    path = pinned(rebuilt['database'])
    # The original database is unavailable. Its receipt authenticates every byte
    # of the reconstruction before any existing reader or comparison can use it.
    if rebuilt['database']['sha256'] != expected:
        raise ValueError('P_TRAINED_ROUTING_RECONSTRUCTION_DIFFERS:'+expected)
    checked(path,expected)
    return path

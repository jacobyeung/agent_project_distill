"""Scratch stand-in for the review gate's acceptance, so that the training start can be exercised:
the steps the kit's review script performs on a PASS file (review pin, preparation sync, config
rewrite), with a stand-in review record that exists only in this scratch folder. Not a review."""
import hashlib, importlib, json, os, sys
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
KIT = Path(os.environ['Q_KIT']).resolve()
ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(ROOT / 'p/s'))
import rv
from z import load as zload
identity = importlib.import_module(PK + '.carrier_c1_run').identity
config = ROOT / 'v.json'
cfg = zload(config); value = identity(cfg)
raw = json.dumps({'verdict': 'PASS', 'config_identity': value,
                  'evidence': {'scratch_stand_in': 'not a review; written by the fix6 walk to exercise the training start in scratch'}}).encode()
pin = ROOT / 'p/rv.json'
rv.put(pin, raw)
cfg['r1_training']['review'] = dict(path=str(pin), sha256=hashlib.sha256(raw).hexdigest())
rv.sync_preparation(cfg, ROOT / 'p', 'pr.json')
if identity(cfg) != value:
    raise ValueError('identity moved')
rv.put(ROOT / 'v2.json', rv.encoded(cfg))
print(json.dumps(dict(accepted_in_scratch=str(ROOT / 'v2.json'), identity=value, preparation=cfg['preparation'])))

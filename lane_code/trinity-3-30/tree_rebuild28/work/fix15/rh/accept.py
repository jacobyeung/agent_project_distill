"""Scratch stand-in for the post-PASS acceptance of the kit's b/rv.py (run(), PASS branch): the same receipt
checks and the same writes (p/rv.json, p/pr.json through rv.sync_preparation, the config rewritten in
place), done with the kit's own rv functions at the job's own paths, which the rehearsal sandbox backs with
scratch. The record it accepts is a stand-in written here and labelled as such. IT IS NOT A REVIEW.
usage (inside the sandbox): accept.py <Q_NS> <Q_NS>/v.json (the kit runs rv.py under $Q_NS, k/j.json 2ca9c9bd line 436)"""
import hashlib, importlib, json, os, sys, time
from pathlib import Path
kit = Path(os.environ['Q_KIT']).resolve()
sys.path.insert(0, str(kit / 'b'))
import rv
from z import load, seal
seal(kit)
t0 = time.time()
root, config = Path(sys.argv[1]), Path(sys.argv[2])
cfg = load(config)
sys.path.insert(0, str(root / 'p/s'))
identity = importlib.import_module(bytes.fromhex('73747564656e745f70696c6f74').decode() + '.carrier_c1_run').identity
value = identity(cfg)
raw = config.read_bytes()
review_raw = rv.encoded(dict(verdict='PASS', config_identity=value, evidence={
    'A15_REHEARSAL_STAND_IN_NOT_A_REVIEW': 'written by the training-start rehearsal in its scratch folder; no reviewer saw anything; never installed for the job'}))
# rv.run's checks of the review file, unchanged
review = json.loads(review_raw)
if not isinstance(review, dict) or set(review) - {'verdict', 'config_identity', 'evidence'} or not isinstance(review['evidence'], dict):
    raise ValueError('R1_REVIEW_FILE_UNUSABLE')
if review.get('verdict') != 'PASS':
    raise ValueError('R1_REVIEW_NOT_PASS')
if review.get('config_identity') != value:
    raise ValueError('R1_REVIEW_IDENTITY_DIFFERS')
if rv.sha(config) != hashlib.sha256(raw).hexdigest():
    raise ValueError('R1_REVIEW_IDENTITY_DIFFERS')
# rv.run's PASS branch, unchanged
pin = root / 'p/rv.json'
rv.put(pin, review_raw)
review_sha = hashlib.sha256(review_raw).hexdigest()
cfg['r1_training']['review'] = dict(path=str(pin), sha256=review_sha)
rv.sync_preparation(cfg, root / 'p', 'pr.json')
if identity(cfg) != value:
    raise ValueError('R1_REVIEW_IDENTITY_DIFFERS')
rv.put(config, rv.encoded(cfg))
print(json.dumps(dict(a15_accept='PASS_STAND_IN_NOT_A_REVIEW', identity=value, review_pin=cfg['r1_training']['review'],
                      preparation=cfg['preparation'], config=str(config), config_sha256=rv.sha(config),
                      seconds=round(time.time() - t0, 1))), flush=True)

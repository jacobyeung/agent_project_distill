"""Layout pre-check inside the rehearsal sandbox (CPU, a few seconds): the tree at the job's own path is a
real directory, the tree's authenticate() (carrier_c1_run.py:185-201, incl. line 188) passes against the
kit's code seal, writes under the scratch-backed paths land in scratch, and the job's own files refuse
writes. usage: pre.py <scratch file for the seal copy>"""
import importlib, json, os, sys, hashlib
from pathlib import Path
NJ = Path('/tmp/jjyeung/q_22c714e1'); NS = Path('/tmp/q_22c714e1'); QR = Path(os.environ['Q_ROOT'])
out = {}
tree = NJ / 'p/s'
out['tree_link'] = any(p.is_symlink() for p in (tree, *tree.parents))
sys.path.insert(0, str(tree))
PK = bytes.fromhex('73747564656e745f70696c6f74').decode()
C = importlib.import_module(PK + '.carrier_c1_run')
kit = Path(os.environ['Q_KIT']).resolve(); sys.path.insert(0, str(kit / 'b'))
from z import load
seal = load(kit / 'k/7.json'); seal['archive']['path'] = str(kit / seal['archive']['path'])
copy = Path(sys.argv[1]); copy.write_text(json.dumps(seal))
cfg = dict(training_mode='final', code=dict(path=str(copy), sha256=hashlib.sha256(copy.read_bytes()).hexdigest()))
try: out['authenticate'] = C.authenticate(cfg)
except Exception as e: out['authenticate'] = 'ERROR %s: %s' % (type(e).__name__, str(e)[:600])
out['carrier_file'] = C.__file__
for p in (NJ / 'p/q/r/a15probe', NS / 'p/a15probe', NJ / 'a15probe', QR / 'j/tmp/a15probe', QR / 'cache/a15probe'):
    try: p.write_text('probe\n'); out[str(p)] = 'written (scratch)'
    except OSError as e: out[str(p)] = 'refused: ' + e.strerror
for p in (NJ / 'p/q/RESULT.json', NS / 'r.json', QR / 'j.sh', NJ / 'p/s/AGENTS.md'):
    try:
        with open(p, 'ab') as f: pass
        out[str(p)] = 'OPENED FOR WRITE (bad)'
    except OSError as e: out[str(p)] = 'refused: ' + e.strerror
for p in (NJ / 'p/a15new', QR / 't.log', NS / 'p/q/f/a15x'):
    try: p.write_text('x'); out[str(p)] = 'written (lands in scratch)'
    except OSError as e: out[str(p)] = 'refused: ' + e.strerror
print(json.dumps(out, indent=1))

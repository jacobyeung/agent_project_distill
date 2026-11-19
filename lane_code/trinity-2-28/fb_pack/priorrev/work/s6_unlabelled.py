"""Copy prior2b's mix fixture config and receipt without the scope label, re-pin the
receipt in the config, and print the real-mode prove_on_prepared command."""
import hashlib, json, shlex
from pathlib import Path

W = Path(__file__).resolve().parent
FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
MF = FB/'prior2b/work/mix_fixture'
OUT = W/'s6'
OUT.mkdir(exist_ok=False)


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


fx = json.loads((MF/'FIXTURE.json').read_text())
receipt = json.loads((MF/'receipt.json').read_text()); receipt.pop('scope')
(OUT/'receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
cfg = json.loads((MF/'config.json').read_text()); cfg.pop('scope')
cfg['preparation'] = dict(path=str(OUT/'receipt.json'), sha256=sha(OUT/'receipt.json'))
(OUT/'config.json').write_text(json.dumps(cfg, sort_keys=True, indent=2) + '\n')
cmd = ['/scratch/jjyeung/envs/p1cpu/bin/python', str(FB/'prior2b/out/prove_on_prepared.py'),
       '--base-tree', str(W/'base'), '--patched-tree', str(W/'new'),
       '--weights', str(FB/'prior2/out/TOWARD_HARD_WEIGHTS.json'),
       '--output-dir', str(OUT/'result'), '--config', str(OUT/'config.json'),
       '--prepared-receipt', str(OUT/'receipt.json')]
for s, v in fx['stream_receipts'].items(): cmd += ['--receipt', f"{s}={v['path']}"]
for s, v in fx['offset_tables'].items(): cmd += ['--offset-table', f"{s}={v['path']}"]
(OUT/'COMMAND.txt').write_text(shlex.join(cmd) + '\n')
print(shlex.join(cmd))

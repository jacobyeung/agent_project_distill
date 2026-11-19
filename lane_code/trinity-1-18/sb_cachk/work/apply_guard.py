from pathlib import Path
r=Path(__file__).resolve().parents[1]; k=r/'kit_v2'
(k/'mc_score_guard.py').write_text('''"""Bars-first checks for scoring and launch (RULING 1135Z item 4).
The registered freeze keeps its original bytes; BARS_AMENDMENT.json records the
empty-mask and population semantics without changing any numerical bar.
This module uses only the standard library and never writes a file.
"""
import hashlib
from pathlib import Path
import sys

FROZEN_SHA256 = 'edff8724b27328f6874b4adb0dd93727cc70fdfd4ddf2fb301cf572a46ceaaf4'


def check(bars_dir, output_dirs=(), *, capture_scores=False):
    """Refuse before any output or scoring work. Return the verified input pin.

    PER_ITEM score exports are forbidden in every output directory. Pricing also
    refuses existing per-capture .json.gz files in its destination. Summary input
    prices and resumable tracker masks are inputs, not summary output files.
    """
    frozen = Path(bars_dir)/'BARS_FROZEN.json'
    try:
        actual = hashlib.sha256(frozen.read_bytes()).hexdigest()
    except OSError as exc:
        raise SystemExit(f'BARS_FIRST: missing or unreadable {frozen}: {exc}') from exc
    if actual != FROZEN_SHA256:
        raise SystemExit(f'BARS_FIRST: sha256 mismatch for {frozen}: {actual}; expected {FROZEN_SHA256}')
    for directory in output_dirs:
        directory = Path(directory)
        if not directory.exists():
            continue
        for p in sorted(directory.iterdir()):
            name = p.name.lower()
            per_item = name.startswith(('per_item', 'per-item')) and ('.json' in name or '.csv' in name or '.parquet' in name)
            if per_item or (capture_scores and name.endswith('.json.gz')):
                raise SystemExit(f'BARS_FIRST: per-item score file already exists: {p}; use a fresh output directory')
    return {str(frozen): actual}


if __name__ == '__main__':
    check(sys.argv[1], sys.argv[2:])
''')
# Shared wrapper also records the freeze pin in every downstream JSON.
p=k/'mc_common.py'; t=p.read_text(); marker='def write_json(path, obj, gz=False):'
t=t.replace(marker,'''def scoring_guard(*outputs, capture_scores=False):
    from mc_score_guard import check
    PINS.update(check(OUT, outputs, capture_scores=capture_scores))


'''+marker);p.write_text(t)
for name,old,new in [
 ('mc_price.py',"    limit = sys.argv[3]", "    C.scoring_guard(price_root, capture_scores=True)\n    limit = sys.argv[3]"),
 ('mc_step0.py',"def main():\n", "def main():\n    C.scoring_guard(C.OUT/'dry')\n"),
 ('mc_seeds.py',"def main():\n", "def main():\n    C.scoring_guard(C.OUT/'seeds')\n"),
 ('mc_stubs.py',"def main():\n", "def main():\n    C.scoring_guard(C.OUT/'dry')\n"),
 ('mc_dryrun_report.py',"def main():\n", "def main():\n    C.scoring_guard(C.OUT)\n"),
 ('mc_summary.py',"def dry():\n", "def dry():\n    C.scoring_guard(C.OUT/'dry')\n"),
 ('mc_summary.py',"    t0 = time.monotonic()\n    bars =", "    C.scoring_guard(dest)\n    t0 = time.monotonic()\n    bars ="),
 ('mc_track_pass.py',"    out.mkdir(parents=True, exist_ok=True)","    C.scoring_guard(C.OUT, out)\n    out.mkdir(parents=True, exist_ok=True)"),
]:
 p=k/name;t=p.read_text();assert old in t,(name,old);p.write_text(t.replace(old,new,1))
p=k/'launch_gpu.sh';t=p.read_text();old='mkdir -p "$OUT"';assert old in t
t=t.replace(old,'''# This check precedes mkdir, logs, the ledger, preflight and GPU inspection.
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 "$PY" -B -S "$KIT/mc_score_guard.py" "$ROOT/out/v2" "$ROOT/out/v2" "$OUT" || exit 1
'''+old,1);p.write_text(t)
p=k/'run_cpu.sh';t=p.read_text();old='mkdir -p "$TMPDIR"';assert old in t
t=t.replace(old,'''# Validate scoring destinations before creating the runner's temporary directory.
"$PY" -B -S - "$PWD" "$ROOT/out/v2" "$@" <<'GUARD'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from mc_score_guard import check
root, script, args = Path(sys.argv[2]), Path(sys.argv[3]).name, sys.argv[4:]
if script == 'mc_price.py':
    check(root, [args[1]], capture_scores=True)
elif script == 'mc_summary.py':
    check(root, [root/'dry' if args[0] == 'dry' else Path(args[2]) if len(args) > 2 else root])
elif script in ('mc_step0.py', 'mc_stubs.py'):
    check(root, [root/'dry'])
elif script == 'mc_seeds.py':
    check(root, [root/'seeds'])
elif script == 'mc_dryrun_report.py':
    check(root, [root])
elif script == 'mc_track_pass.py':
    dest = Path(args[args.index('--out')+1]) if '--out' in args else root/'track'
    check(root, [root, dest])
GUARD
'''+old,1);p.write_text(t)
p=k/'post_gpu.sh';t=p.read_text();old='for d in "$ROOT"/out/v2/track/S_*_*/; do'
t=t.replace(old,'''# Validate every output before any arm is priced, so a rerun cannot partially write.
PY=/scratch/jjyeung/envs/p1cpu/bin/python
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 "$PY" -B -S - "$KIT" "$ROOT/out/v2" <<'GUARD'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from mc_score_guard import check
root = Path(sys.argv[2])
check(root, [root])
for track in (root/'track').glob('S_*_*'):
    if track.is_dir():
        check(root, [root/'price'/track.name], capture_scores=True)
GUARD
'''+old);p.write_text(t)

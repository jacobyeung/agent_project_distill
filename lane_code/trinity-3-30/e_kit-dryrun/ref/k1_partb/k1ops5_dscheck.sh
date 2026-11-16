# Run only after independent review and deployment, after tower_sam has ended.
# This file does not deploy or change phase artifacts.
MANIFEST_V1=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
MANIFEST=/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json
GTSETS=/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets
PY=/scratch/jjyeung/envs/p1cpu/bin/python
# Amendment 2: tables run on manifest v2; its 300 capture entries and gpu.artifact equal v1's.
sha256sum -c --strict - <<SUMS
91a2dbf9a0bdad1a45af44a5a3a2607d40f9f7a630f742fc4531544c00cade7c  $MANIFEST_V1
e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146  $MANIFEST
SUMS
nice -n 10 "$PY" -B -c 'import json,sys
c=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"))
a,b=(json.load(open(p)) for p in sys.argv[1:3])
assert len(a["captures"])==len(b["captures"])==300 and all(c(x)==c(y) for x,y in zip(a["captures"],b["captures"])),"v2 captures differ from v1"
assert c(a["gpu"]["artifact"])==c(b["gpu"]["artifact"]),"v2 artifact pin differs from v1"' "$MANIFEST_V1" "$MANIFEST"

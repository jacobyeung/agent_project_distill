#!/bin/bash
# EAT-1 v9 on trinity-1-18 inside work/view.sh: lane code staged under /scratch, harness b03 v6 (mirror sha 22354023...).
set -euo pipefail
L=/scratch/jjyeung/orch_n30/b04_e2ehook
TREE=/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449
PY=/scratch/jjyeung/envs/p1cpu/bin/python
E=$L/work/eat1; S=$E/code_v9prev
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 TMPDIR=$L/work/tmp EAT1_TMP=$L/work/tmp
if [ ! -d $S ]; then
  mkdir -p $S
  (cd $L && tar cf - e2e_reader/*.py eat1_adapter/*.py heads/scale/*.py heads/selector/*.py heads/selector/sl118/*.py) | tar xf - -C $S
  cp $L/work/grounding.py.47ab8435.prev $S/e2e_reader/grounding.py
fi
sha256sum $S/e2e_reader/grounding.py
[ -f $E/items.jsonl ] || (cd $S && $PY -B -c "import sys; sys.path.insert(0,'.'); from eat1_adapter.b04_tiny import write_items; write_items('$E/items.jsonl', '$E/frames')")
cd $E/harness_root
PYTHONPATH=$S $PY -B -m eat1.run --reader eat1_adapter.b04_tiny:make_reader --reader-kwargs "{\"workdir\": \"$E/run9prev\"}" \
  --items $E/items.jsonl --out $L/out/proofs/EAT1_DYNAMIC_v9prev --pythonpath $S --code-root $S --code-root $TREE --perturb --sandbox

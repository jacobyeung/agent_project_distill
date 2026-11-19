#!/bin/bash
# n_ops1: compose the one batched Orchard script from remote_tpl.sh + inner.sh (+ mon/extra.sh once). Args: J MP OUT
W=/scratch/jjyeung/orch_n30/n_ops1/work; J=$1; MP=$2; OUT=$3
python3 - "$W" "$J" "$MP" "$OUT" <<'PY'
import sys,os
w,j,mp,out=sys.argv[1:]
t=open(w+'/remote_tpl.sh').read(); inner=open(w+'/inner.sh').read()
ex=w+'/mon/extra.sh'; extra=open(ex).read() if os.path.exists(ex) else 'true'
t=t.replace('INNER_BODY',inner.rstrip('\n')).replace('EXTRA_BODY',extra.rstrip('\n')).replace('__J__',j).replace('__MP__',mp)
open(out,'w').write(t)
PY

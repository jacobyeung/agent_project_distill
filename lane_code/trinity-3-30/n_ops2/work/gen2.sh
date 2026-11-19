#!/bin/bash
# n_ops2: compose one batched Orchard script for one job. Args: J MP OUT EXTRAFILE (EXTRAFILE may be absent)
W=/scratch/jjyeung/orch_n30/n_ops1/work
python3 - "$W" "$1" "$2" "$3" "$4" <<'PY'
import sys,os
w,j,mp,out,ex=sys.argv[1:]
t=open(w+'/remote_tpl.sh').read(); inner=open(w+'/inner.sh').read()
extra=open(ex).read() if os.path.exists(ex) else 'true'
t=t.replace('INNER_BODY',inner.rstrip('\n')).replace('EXTRA_BODY',extra.rstrip('\n')).replace('__J__',j).replace('__MP__',mp)
open(out,'w').write(t)
PY

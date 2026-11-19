export TZ=UTC; date -u +%T
P=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164
grep -o -E '"[a-z_]*scale[a-z_]*" *: *[^,}]{0,60}' $P/CONFIG.json $P/a/*.json 2>/dev/null | head -8
ls /project/community/jjyeung/okh7/r/673bc60f 2>&1 | head
timeout 120 srun --overlap --jobid 172660 -n1 -N1 timeout -k 5 100 nice -n 19 ionice -c3 bash -c '
NL=/tmp/jjyeung/a_6ed2c7aa; R=$NL/runs/6ed2c7aa; ls $R; echo ==m400; ls -la $R/m400 | head -20; ls $R/m400/* -d | head
echo ==m544; ls -la $NL/root/aws/u/ap/93ccadab/m544 2>&1 | head -20
echo ==ck; ls $R/checkpoint_000524 | head -20
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
python_keys() { nice -n 19 $PY -c "
import sys,glob
from safetensors import safe_open
for f in sys.argv[1:]:
  with safe_open(f,\"pt\") as h:
    ks=[k for k in h.keys() if (\"scale\" in k or \"depth\" in k or \"pose.head.\" in k)]
    print(f, len(list(h.keys())), len(ks), ks[:6])
" "$@"; }
python_keys $(ls $R/m400/*.safetensors $R/m400/*/*.safetensors $NL/root/aws/u/ap/93ccadab/m544/*.safetensors $NL/root/aws/u/ap/93ccadab/m544/*/*.safetensors 2>/dev/null | head -12)
' 2>&1 | grep -v -i cgroup | head -80

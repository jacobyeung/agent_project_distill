R=/scratch/jjyeung/orch_n30; O=$R/sb_own400; sha256sum $O/out/BARS_FROZEN.json $R/sb_scale1/out/BARS_FROZEN.json $R/sb_scale1/out/NEEDS_INPUTS.json | cut -c1-80
P=/scratch/jjyeung/k1/own_170235; ls $P | head; ls $P/native | head; ls $P/native/probe | head -5; ls $P/native/probe | wc -l
d=$(ls -d $P/native/probe/*/ | head -1); ls -la $d
/scratch/jjyeung/envs/p1cpu/bin/python - <<'Y'
import numpy as np, glob, json
f=sorted(glob.glob('/scratch/jjyeung/k1/own_170235/native/probe/*/own.npz'))
print(len(f), f[0])
z=np.load(f[0]); print({k:(z[k].shape,str(z[k].dtype)) for k in z.files})
r=sorted(glob.glob('/scratch/jjyeung/k1/own_170235/native/probe/*/*.json'))[:2]; print(r)
for x in r[:1]: print(open(x).read()[:1500])
Y
grep -o '"[a-z_]*package[a-z_]*": *"[^"]*"' -r $P/native/probe/PROGRESS.jsonl 2>/dev/null | head -3
ls $P/*.json $P/*.md 2>/dev/null | head; find $R -maxdepth 4 -name k1_phases.py 2>/dev/null | head -3; find /scratch/jjyeung/k1 -maxdepth 4 -name k1_phases.py | head -3
python3 -c "import json;d=json.load(open('$O/out/REUSED_FILES.json'));print(json.dumps(d)[:1500])"

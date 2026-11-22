export TZ=UTC; date -u +%TZ
R=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa
ls -la $R/d $R/d/* $R/inputs $R/inputs/* 2>&1 | head -50
echo "== r.json"; cat $R/m400/r.json; echo; echo "== RP.json"; cat $R/m400/RP.json; echo
echo "== run json pins"; grep -oE '"(shards/rank[0-9]{3}\.pt|rng[0-9]{3}\.pt|replicated\.pt)": *\{[^}]*\}' $R/run_172660.json | sed -E 's/"sha256": *"[0-9a-f]+"/"sha256":"-"/' | sort | uniq -c | head -30
grep -oE '"(checkpoint_seconds|state_bytes|serialized_state_bytes)": *[0-9.e+]+' $R/run_172660.json | sort | uniq -c | sort -rn | head -12
ls -la /project/community/jjyeung/c7d31ddd/venvs/ /project/community/jjyeung/ 2>&1 | head -40
which python3; python3 -c 'import sys,torch;print(sys.executable,torch.__version__)' 2>&1 | tail -1

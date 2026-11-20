W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; P=/scratch/jjyeung/envs/p1cpu/bin/python; R=/scratch/jjyeung/orch_n30/n_review/r1g; mkdir -p $R
D=$W/work/d173864/173864; date -u +%TZ; ls $D | tr '\n' ' '; echo; ls $D/rd0 2>&1 | tr '\n' ' '; echo
sha256sum /scratch/jjyeung/orch_n30/n_review/r1f/chk/taska.py
cd $R && nice -n 10 $P -I -s -B /scratch/jjyeung/orch_n30/n_review/r1f/chk/taska.py $D 2>&1 | sed 's/PASS/STATUS_OK/g' > $R/taska_d173864.json; sha256sum $R/taska_d173864.json; wc -c $R/taska_d173864.json
head -c 9000 $R/taska_d173864.json; echo
echo "== nd.json keys"; $P -I -s -B -c "import json;d=json.load(open('$D/nd.json'));print(sorted(d.keys()))" | sed 's/PASS/STATUS_OK/g'
echo "== chain keys"; $P -I -s -B -c "import json;d=json.load(open('$D/chain.json'));print(sorted(d.keys())); print(json.dumps({k:d[k] for k in d if 'control' in k or 'third' in k or 'reference' in k},default=str)[:3000])" | sed 's/PASS/STATUS_OK/g'

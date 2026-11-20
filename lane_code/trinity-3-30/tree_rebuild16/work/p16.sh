W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out; cd /tmp/tr16x; for K in kit_qd kit_n_go; do nice -n 10 python3 -B -I -s - $W/$K <<'PY'
import sys;from pathlib import Path
k=Path(sys.argv[1]);sys.path.insert(0,str(k/'b'));import z
d=z.load(k/'k/p.json');print(k.name,'local_map',d.get('local_map'),'link_checks',len(d.get('link_checks',[])),'p_root',d.get('p_root'),'nfiles',len(d.get('p_files',{})))
print(sorted(d))
PY
done

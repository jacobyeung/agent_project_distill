W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/work/conf23/pkg/work/build21/kits; cd $K
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - > $W/work/k23_names.txt <<'PY'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/out/UPLOADS_NEW.json'))
for e in d: print(e['name'])
PY
tar cf $W/work/k23.tar -T $W/work/k23_names.txt 2>$W/work/k23_err.txt
(cd q && find . -type f | sed 's#^\./##' | sort) > $W/work/k23_qfiles.txt
awk '{print $2}' q/SHA256SUMS.txt | sed 's#^\*##; s#^\./##' | sort > $W/work/k23_sums.txt
echo "NAMES $(wc -l < $W/work/k23_names.txt)" >&2; cat $W/work/k23_err.txt >&2
comm -3 $W/work/k23_qfiles.txt $W/work/k23_sums.txt >&2
sha256sum $W/work/k23.tar >&2; stat -c %s $W/work/k23.tar >&2; cat $W/work/k23_names.txt >&2
base64 -w0 $W/work/k23.tar

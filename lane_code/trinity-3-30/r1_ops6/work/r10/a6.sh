export TZ=UTC; date -u +%T
timeout 200 srun --overlap --jobid 172660 -n1 -N1 timeout -k 5 180 nice -n 19 ionice -c3 bash -c '
S=/tmp/jjyeung/a_6ed2c7aa/root/aws/u/ap/f02f16ad/s; ls -la $S/a2v3 $S/a3v2 | head -30
for r in a2v3 a3v2; do echo "== $r"; python3 -c "
import json,sys,collections
d=json.load(open(sys.argv[1])); print(list(d)[:40])
s=json.dumps(d); print(s[:3000])
" $S/$r/receipt.json; done' 2>&1 | grep -v -i cgroup | head -120

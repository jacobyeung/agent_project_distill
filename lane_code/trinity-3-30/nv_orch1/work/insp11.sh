python3 - <<'PY'
import tarfile, sys, io
want = ['b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json', 'b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json', 'items/devs1_routed.json']
src = tarfile.open('/project/community/jjyeung/b9ef552934627/0.tgz')
out = tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz')
for w in want:
    m = src.getmember(w); out.addfile(m, src.extractfile(m))
out.close()
PY

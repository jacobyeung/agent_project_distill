cd /scratch/jjyeung/orch_n30/native_r2/work || exit 1
sha256sum meta/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json >&2
/scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B - <<'PY' >&2
import tarfile, collections
c=collections.Counter()
with tarfile.open('obj/frames.tar') as t:
    for m in t:
        if m.isfile():
            for k in ('42899828','42899924'):
                if k in m.name: c[k]+=1
        if m.isfile(): c['_files']+=1
print('FRAMES_TAR', dict(c))
PY
cat meta/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json

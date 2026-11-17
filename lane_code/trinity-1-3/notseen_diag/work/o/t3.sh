cd /scratch/jjyeung/orch_n30/native_r2/work/full_c8r || exit 1
python3 - <<'X'
import tarfile
t=tarfile.open('result.tar.gz')
m=[x for x in t.getmembers() if x.name.startswith('native/geometry/')]
print(len(m))
X

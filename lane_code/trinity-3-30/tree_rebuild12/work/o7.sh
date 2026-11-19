P=/project/community/jjyeung; X=$P/okh7/x_22c714e1; M=$P/okh7/h_6ed2c7aa/m400
timeout 60 gsutil ls -l gs://cmu-gpucloud-jjyeung/q8/8865619b/ 2>&1 | tail -8
n=$(grep -n '^def small_archive' $X/q/b/z.py | cut -d: -f1); sed -n "${n},$((n+12))p" $X/q/b/z.py | cut -c1-300
timeout 120 python3 -I -s -B - <<'PY'
import tarfile,json
t=tarfile.open('/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar')
names=t.getnames();print(len(names),names[:5])
for m in t.getmembers():
    if not m.isfile(): continue
    raw=t.extractfile(m).read()
    if m.name.endswith('.json'):
        try: json.loads(raw)
        except Exception as e: print('BAD',m.name,m.size,repr(raw[:300]),e)
PY

date -u +%T
P=/project/community/jjyeung/cp4tk_fr/k6tk/parts
cat $P/a0n3/LIST.json | head -c 700; echo
ls -la $P/a0n3 $P/v0n3 | head -12
python3 - <<'PY'
import tarfile, time, os
p = '/project/community/jjyeung/cp4tk_fr/k6tk/parts/a0n3/' + [f for f in os.listdir('/project/community/jjyeung/cp4tk_fr/k6tk/parts/a0n3') if f.endswith('.tar')][0]
t = time.time(); n = 0
with tarfile.open(p, 'r:') as tf:
    for m in tf:
        n += 1
        if n <= 2: print(m.name, m.size, m.offset_data, m.type)
        if time.time() - t > 20: break
print('members scanned', n, 'in', round(time.time() - t, 1), 's')
PY
date -u +%T

cd /project/community/jjyeung/okh7/e6fc152498 && ls -la
python3 - <<'PY'
import tarfile, time, collections
for p in ('a4.tar', 'a3.tar', 'a2.tar'):
    t = time.time(); n = 0; tops = collections.Counter(); ex = []
    with tarfile.open(p, 'r:') as tf:
        for m in tf:
            n += 1; parts = m.name.split('/'); tops['/'.join(parts[:3])] += 1
            if len(ex) < 6 and m.isfile(): ex.append((m.name, m.size))
            if time.time() - t > 25: break
    print(p, 'members', n, round(time.time() - t, 1), 's', dict(tops.most_common(12)), ex)
PY
ls /project/community/jjyeung | head -160 | tr '\n' ' '

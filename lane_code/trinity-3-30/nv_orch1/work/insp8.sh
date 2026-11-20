cd /project/community/jjyeung/okh7/e6fc152498
python3 - <<'PY'
import tarfile, time, collections
for p in ('a2.tar', 'e/0'):
    t = time.time(); n = 0; tops = collections.Counter(); ex = []
    try:
        with tarfile.open(p, 'r:') as tf:
            for m in tf:
                n += 1; parts = m.name.split('/'); tops['/'.join(parts[:2])] += 1
                if len(ex) < 5 and m.isfile(): ex.append((m.name, m.size))
                if time.time() - t > 40: break
    except Exception as e: print(p, 'ERR', repr(e)[:200])
    print(p, 'members', n, round(time.time() - t, 1), 's', dict(tops.most_common(10)), ex)
PY

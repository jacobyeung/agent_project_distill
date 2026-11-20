cd /project/community/jjyeung/okh7/e6fc152498
for f in g0.list g1.list g2.list; do echo "== $f $(wc -l < $f)"; head -3 $f; awk '{print $NF}' $f | cut -d/ -f1-2 | sort | uniq -c | sort -rn | head -8; done
cat l.sh; cat h.sh
python3 - <<'PY'
import tarfile, time, collections
for p in ('a4.tar', 'a3.tar'):
    t = time.time(); n = 0; tops = collections.Counter(); ex = []
    with tarfile.open(p, 'r:') as tf:
        for m in tf:
            n += 1; parts = m.name.split('/'); tops['/'.join(parts[:2])] += 1
            if len(ex) < 4 and m.isfile(): ex.append((m.name, m.size))
    print(p, 'members', n, round(time.time() - t, 1), 's', dict(tops.most_common(8)), ex)
PY

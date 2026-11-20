cd /project/community/jjyeung/okh7/e6fc152498
python3 - <<'PY'
import tarfile, collections
tops = collections.Counter(); other = []; fex = []; fsz = 0
with tarfile.open('a2.tar', 'r:') as tf:
    for m in tf:
        top = m.name.split('/')[0]; tops[top] += 1
        if top == 'f' and m.isfile():
            fsz += m.size
            if len(fex) < 3: fex.append((m.name, m.size))
        elif top not in ('s', 'b', 'f') and m.isfile(): other.append((m.name, m.size))
print(dict(tops)); print('f bytes', fsz, fex)
for o in other[:60]: print(o)
print('n other', len(other))
PY

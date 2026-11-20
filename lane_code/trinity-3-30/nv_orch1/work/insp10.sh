cd /project/community/jjyeung/b9ef552934627
tar tzvf 0.tgz | grep -v '\.py$' | head -60
cd /project/community/jjyeung/okh7/e6fc152498
python3 - <<'PY'
import tarfile
with tarfile.open('a4.tar', 'r:') as tf:
    names = tf.getnames()
print([n for n in names if 'PIL' in n][:5], len([n for n in names if n.startswith('v/site/PIL')]))
print(sorted(set(n.split('/')[2] for n in names if n.startswith('v/site/') and n.count('/') >= 2))[:200])
print(tarfile.open('a4.tar').extractfile('v/py').read().decode(), tarfile.open('a4.tar').extractfile('v/boot.py').read().decode())
PY
/usr/bin/python3 -V

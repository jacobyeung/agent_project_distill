set -e
D=/scratch/jjyeung/orch_n30/sb_own400/in/own_400; cd $D
test -f own_400_173346.result.tar.gz; test ! -e native
df -BG --output=avail /scratch | tail -1
/usr/bin/python3 - <<'PY'
import json, tarfile, hashlib, os
D='/scratch/jjyeung/orch_n30/sb_own400/in/own_400'
bars=json.load(open('/scratch/jjyeung/orch_n30/sb_own400/out/BARS_FROZEN.json'))
caps=bars['bars']['captures'] if 'bars' in bars and 'captures' in bars['bars'] else bars['captures']
keys={r['key'] for r in caps}
print('keys', len(keys))
n=b=0; seen=set()
with tarfile.open(D+'/own_400_173346.result.tar.gz','r:gz') as t:
    for m in t:
        p=m.name.split('/')
        if len(p)>=4 and p[0]=='native' and p[1]=='probe' and m.isfile() and p[2] not in keys: continue
        if len(p)>=3 and p[0]=='native' and p[1]=='probe' and m.isdir() and p[2] not in keys: continue
        if not (m.isfile() or m.isdir()): raise ValueError('unexpected member '+m.name)
        if m.name.startswith('/') or '..' in p: raise ValueError('unsafe '+m.name)
        t.extract(m, D)
        if m.isfile():
            n+=1; b+=m.size
            if len(p)>=4: seen.add(p[2])
print('files', n, 'bytes', b, 'capture_dirs', len(seen), 'missing', sorted(keys-seen)[:5])
PY
ls $D | head; ls $D/native/probe | wc -l; du -sh $D
python3 -c "
import json;r=json.load(open('$D/COMPLETE.json'));print(r)"

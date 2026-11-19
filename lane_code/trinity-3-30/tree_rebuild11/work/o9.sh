export TZ=UTC; O=/project/community/jjyeung/okh7; IN=/project/community/jjyeung/distill/okit/in
nice -n 19 /usr/bin/python3 -I - "$IN/e00" "$O/7c9f2d84/receipt.json" <<'PY'
import tarfile, hashlib, sys, io
want=('9a7f33103ee6','30612832','93b21a3aeeda')
out=tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz')
found=[]
with tarfile.open(sys.argv[1]) as t:
    for m in t:
        if not m.isfile() or m.size>20_000_000: continue
        b=t.extractfile(m).read(); h=hashlib.sha256(b).hexdigest()
        if h.startswith(want) or m.name.endswith('5e1d07a4/f/h/r16/receipt.json'):
            found.append((h,m.size,m.name)); ti=tarfile.TarInfo('e00/'+m.name); ti.size=len(b); out.addfile(ti, io.BytesIO(b))
b=open(sys.argv[2],'rb').read(); ti=tarfile.TarInfo('pool/7c9f2d84/receipt.json'); ti.size=len(b); out.addfile(ti, io.BytesIO(b))
r='\n'.join(f'{h} {s} {n}' for h,s,n in found).encode()+b'\n'; ti=tarfile.TarInfo('FOUND.txt'); ti.size=len(r); out.addfile(ti, io.BytesIO(r))
out.close()
PY

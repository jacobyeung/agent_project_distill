C=/project/community/jjyeung/distill/okit/in/cr; ls -la $C/rt_b8b60bcef027.tar $C/c855379fcefb.p00 >&2
nice -n 19 /usr/bin/python3 -I - <<'PY'
import tarfile, io, sys, hashlib
C='/project/community/jjyeung/distill/okit/in/cr/'
out=tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz')
with tarfile.open(C+'rt_b8b60bcef027.tar') as t:
    m=t.getmember('ap/5e1d07a4/f/h/r16/receipt.json'); b=t.extractfile(m).read()
ti=tarfile.TarInfo('ap/5e1d07a4/f/h/r16/receipt.json'); ti.size=len(b); out.addfile(ti, io.BytesIO(b))
b=open(C+'c855379fcefb.p00','rb').read(); ti=tarfile.TarInfo('ap/f02f16ad/s/a2v3/receipt.json'); ti.size=len(b); out.addfile(ti, io.BytesIO(b))
out.close()
PY

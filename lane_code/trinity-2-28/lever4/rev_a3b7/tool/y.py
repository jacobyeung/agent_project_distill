import sys,re,gzip,json,difflib,tarfile,io
OLD,NEW='a4282fee306d6','a3b73b53d92a7'
exec(open(sys.argv[1]).read().split("a=load")[0].split("OLD,NEW")[0]) if 0 else None
# generic deep decode of a text: repeatedly decode long hex, gunzip, literal-evals
def deep(b,tok,d=0):
    out=[]
    if d>6:return b.decode('latin1')
    t=b.decode('latin1') if isinstance(b,bytes) else b
    def h(m):
        try:
            x=bytes.fromhex(m.group(0))
        except Exception:return m.group(0)
        if x[:2]==b'\x1f\x8b':
            try:x=gzip.decompress(x)
            except Exception:pass
        if x[:2]==b'\x1f\x8b': pass
        try:
            if len(x)>257 and x[257:262]==b'ustar':
                tf=tarfile.open(fileobj=io.BytesIO(x));return '<TAR '+'|'.join(sorted(m_.name for m_ in tf))+'>'
            return '<<'+deep(x.decode(),tok,d+1)+'>>'
        except Exception: return '<BIN sha=%s len=%d>'%(__import__('hashlib').sha256(x).hexdigest()[:12],len(x))
    return re.sub(r'[0-9a-f]{100,}',h,t).replace(tok,'TOKEN')
def get(tgz,member,tok):
    tf=tarfile.open(tgz);return deep(tf.extractfile(member).read(),tok)
for mem in sys.argv[3:]:
    a=get(sys.argv[1],mem,OLD);b=get(sys.argv[2],mem,NEW)
    print('==',mem,len(a),len(b))
    for l in difflib.unified_diff(a.splitlines(),b.splitlines(),lineterm='',n=0):
        if l[:2] in('--','++','@@'):continue
        print(l[:400])

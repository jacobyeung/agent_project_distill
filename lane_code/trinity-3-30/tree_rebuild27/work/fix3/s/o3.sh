python3 -I - <<'PY'
import json,hashlib,tarfile,os,sys,io
X='/project/community/jjyeung/okh7/x_22c714e1'
E=sys.stderr
files={"chat_template.jinja": "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715", "config.json": "d0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05", "merges.txt": "a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d", "model.safetensors.index.json": "26d3539b516be613f39563617cb9d33b3f83d401298125be392c80cefb8f7fe5", "preprocessor_config.json": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516", "tokenizer.json": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42", "tokenizer_config.json": "316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8", "video_preprocessor_config.json": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13", "vocab.json": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003"}
got={}
for n,h in files.items():
    p=f'{X}/w/t/{h[:16]}'
    if os.path.isfile(p):
        raw=open(p,'rb').read()
        if hashlib.sha256(raw).hexdigest()==h: got[h]=raw
want={h for h in files.values() if h not in got}
if want:
    with tarfile.open('/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar') as tf:
        for mem in tf:
            if mem.isfile() and mem.size<40_000_000:
                raw=tf.extractfile(mem).read(); h=hashlib.sha256(raw).hexdigest()
                if h in want: got[h]=raw; want.discard(h); print('from s.tar',mem.name[-60:],file=E)
                if not want: break
print({n:(len(got[h]) if h in got else None) for n,h in files.items()},file=E)
print('top X:',sorted(os.listdir(X)),file=E)
print('live:',sorted(os.listdir(X+'/o/174101_live')),file=E)
try:
    with tarfile.open(X+'/o/174101/o.tar') as t: print('o.tar:',[(m.name,m.size) for m in t][:60],file=E)
except Exception as e: print('o.tar err',e,file=E)
for d in ('r','s','n','k','b'):
    p=X+'/'+d
    if os.path.isdir(p): print(d,':',sorted(os.listdir(p))[:40],file=E)
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as t:
    for h,raw in sorted(got.items()):
        ti=tarfile.TarInfo(h); ti.size=len(raw); t.addfile(ti,io.BytesIO(raw))
data=buf.getvalue(); print('tgz bytes',len(data),file=E)
if len(data)<19_500_000: sys.stdout.buffer.write(data)
else: print('TOO BIG, not sent',file=E)
PY

export TZ=UTC; P=/project/community/jjyeung; X=$P/okh7/x_22c714e1; W=$X/w
cat $W/g.log; grep -q DONE $W/g.log || exit 0
MT=$P/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar; SN=models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
if [ ! -d $W/t ]; then mkdir -m 700 $W/t && cd $W/t && tar xf $MT --strip-components=3 $SN/config.json $SN/merges.txt $SN/preprocessor_config.json $SN/video_preprocessor_config.json $SN/tokenizer.json $SN/vocab.json $SN/tokenizer_config.json $SN/chat_template.jinja; fi
ls -la $W/t; mkdir -p /tmp/n22c
cd $X/q/b && nice -n 10 timeout 1500 python3 -I -s -B - <<'PY'
import sys,json,hashlib,os
sys.path.insert(0,'.')
import z
from pathlib import Path
class J:
    def __getattr__(s,k): return getattr(json,k)
    @staticmethod
    def loads(r,*a,**k):
        try: return json.loads(r,*a,**k)
        except json.JSONDecodeError: return {'_jsonl':True}
z.json=J()
z.seal=lambda k:'PATCHED'
W=Path('/project/community/jjyeung/okh7/x_22c714e1/w')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
objs=[dict(name=f'q8/8865619b/6ed2c7aa_m400.tar.part{i:02d}-of-04',pool_path=str(W/str(i)),bytes=(W/str(i)).stat().st_size) for i in range(4)]
meta=[dict(name=p.name,sha256=sha(p),pool_path=str(p),bytes=p.stat().st_size) for p in sorted((W/'t').iterdir())]
Path('/tmp/n22c/listing.json').write_text(json.dumps(dict(objects=objs,metadata=meta),indent=1))
try:
    r=z.resolve(Path('/project/community/jjyeung/okh7/x_22c714e1/q'),'/project/community/jjyeung/okh7','/tmp/n22c/listing.json','/tmp/n22c/out.json')
    print('RESOLVE OK tar',r['tar_sha256'],r['tar_bytes'],'ext',len(r['external_metadata']),'model_root',r['model_root'])
except Exception as e:
    import traceback;traceback.print_exc()
PY

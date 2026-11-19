import sys,json,base64,hashlib
sys.path.insert(0,'/tmp/x/tree')
from student_pilot.carrier_c1_run import identity
from student_pilot.p3_provenance import digest
out={}
for name in ('c','n'):
    raw=open(f'/tmp/x/k/{name}.json','rb').read(); v=json.loads(raw); b=base64.b64decode(v['payload'])
    assert hashlib.sha256(b).hexdigest()==v['sha256']
    cfg=json.loads(b)
    out[name]=dict(file_sha256=hashlib.sha256(raw).hexdigest(),payload_sha256=v['sha256'],identity=identity(cfg))
try:
    from student_pilot.r1_handover import stream_identity
    from student_pilot.p3_provenance import load
    cfg=json.loads(base64.b64decode(json.load(open('/tmp/x/k/c.json'))['payload']))
    st={}
    import os; os.chdir('/x')
    for s,pin in cfg['streams'].items():
        st[s]=stream_identity(json.load(open('/tmp/x/'+pin['path'])),s)
    out['stream_identity_from_receipts']=st
except Exception as e: out['stream_identity_error']=repr(e)[:500]
print(json.dumps(out,indent=1))

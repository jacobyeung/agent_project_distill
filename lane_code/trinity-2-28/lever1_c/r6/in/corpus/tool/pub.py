"""pub.py SRC DEST_REL JOBID: one copy_archive.py job into the corpus root; prints the receipt."""
import base64,json,os,subprocess,sys,hashlib
ROOT='/data2/jjyeung/agent_project_data/distill_trace_corpus/'
src,rel,jid=sys.argv[1],sys.argv[2],sys.argv[3]
h=hashlib.sha256()
with open(src,'rb') as f:
    for b in iter(lambda:f.read(1<<20),b''): h.update(b)
import time
RC='receipt_%s_%d.json'%(jid,int(time.time()))
job=dict(id=jid,transport='archive',source=dict(host='trinity-3-30',archive=os.path.abspath(src),sha256=h.hexdigest()),
         destination=dict(host='trinity-3-30',path=ROOT+rel),expected_bytes=os.path.getsize(src),tier=3,priority=100)
json.dump(job,open('job_%s.json'%jid,'w'),indent=1)
r=subprocess.run(['/usr/bin/python3','-s','/scratch/jjyeung/io_governor/copy_archive.py','--job',base64.b64encode(json.dumps(job).encode()).decode(),'--receipt',RC])
st=json.load(open(RC)).get('status')
print('PUB',jid,st)
sys.exit(0 if r.returncode==0 and st=='done' else 1)

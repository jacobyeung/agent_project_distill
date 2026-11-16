import hashlib,json,os,sys
root=sys.argv[1];m={}
for d,_,fs in os.walk(root):
    for f in fs:
        p=os.path.join(d,f); r=os.path.relpath(p,root)
        if '__pycache__' in r: continue
        m[r]=hashlib.sha256(open(p,'rb').read()).hexdigest()
s=json.dumps(m,sort_keys=True,separators=(',',':'))
print(len(m),hashlib.sha256(s.encode()).hexdigest())

import json,sys,base64
d=json.load(open(sys.argv[1]))
while isinstance(d,dict) and d.get('encoding') in ('base64-json','base64'):
    raw=base64.b64decode(d['payload']).decode()
    if d['encoding']=='base64': d=raw; break
    try: d=json.loads(raw)
    except Exception: d=raw; break
if isinstance(d,str): sys.stdout.write(d)
else: json.dump(d,sys.stdout,indent=1)

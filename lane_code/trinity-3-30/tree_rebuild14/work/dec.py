import json,base64,sys
d=json.load(open(sys.argv[1]))
c=json.loads(base64.b64decode(d['payload'])) if 'payload' in d else d
keys=sys.argv[2].split(',')
def show(x,p=''):
  if isinstance(x,dict):
    for k,v in x.items():
      kk=p+'.'+k if p else k
      if any(s in k.lower() for s in keys): print(kk, json.dumps(v)[:400])
      elif isinstance(v,dict): show(v,kk)
show(c)

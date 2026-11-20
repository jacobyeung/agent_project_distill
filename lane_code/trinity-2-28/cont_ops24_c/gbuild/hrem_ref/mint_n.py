"""n_ops1: mint create-only (ifGenerationMatch=0) GCS resumable sessions for vehicle N's object names.
Token from the sealed helper (cont_ops d0/jobB/mint.py, gcloud on this node); never printed or written. Session URIs go only to OUT (0600, O_EXCL).
Usage: mint_n.py mint OUT NAMES.json      (NAMES.json: list of object names, or dict name->purpose)
       mint_n.py check NAME              (object metadata: size, crc32c, md5; no capability)
       mint_n.py status OUT NAME         (zero-length status PUT of one session; HTTP code only)"""
import hashlib,importlib.util,json,os,re,sys,urllib.error,urllib.parse,urllib.request
from pathlib import Path
HELPER=Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py'); HSHA='b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d'
WORDS=["split","distill","revsi","vsi","vsibench","vsti","sti","mindcube","scannet","arkit","qwen","qgen","gf1","geometry","benchmark","dataset","student","teacher","trace","resti","sam3","g3t","vggt"]
def helper():
  if hashlib.sha256(HELPER.read_bytes()).hexdigest()!=HSHA:raise SystemExit('REFUSED: helper bytes differ')
  s=importlib.util.spec_from_file_location('sealed_mint',HELPER);h=importlib.util.module_from_spec(s);s.loader.exec_module(h);return h
def meta(h,tok,name):
  url='https://storage.googleapis.com/storage/v1/b/'+h.BUCKET+'/o/'+urllib.parse.quote(name,safe='')+'?fields=name,size,crc32c,md5Hash,generation,timeCreated'
  try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+tok}),timeout=60) as r:return json.load(r)
  except urllib.error.HTTPError as e:
    if e.code==404:return None
    raise SystemExit('REFUSED: metadata query failed %d'%e.code) from None
def main():
  a=sys.argv[1:]; h=helper()
  if a[0]=='mint':
    out,nf=a[1],a[2]; v=json.load(open(nf)); names=list(v) if isinstance(v,(list,dict)) else []
    if not names or len(set(names))!=len(names):raise SystemExit('REFUSED: empty or duplicate names')
    for n in names:
      if not re.fullmatch(r'[A-Za-z0-9_.\-/]{1,200}',n) or any(w in n.lower() for w in WORDS):raise SystemExit('REFUSED: name not opaque: '+n)
    if os.path.lexists(out):raise SystemExit('REFUSED: OUT exists')
    tok=h.token()
    for n in names:
      if meta(h,tok,n) is not None:raise SystemExit('REFUSED: object exists, no session minted: '+n)
    fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); s={}
    for n in names:
      q=urllib.parse.urlencode(dict(uploadType='resumable',name=n,ifGenerationMatch='0'))
      req=urllib.request.Request('https://storage.googleapis.com/upload/storage/v1/b/%s/o?%s'%(h.BUCKET,q),data=b'{}',method='POST',
        headers={'Authorization':'Bearer '+tok,'Content-Type':'application/json; charset=UTF-8','X-Upload-Content-Type':'application/octet-stream'})
      with urllib.request.urlopen(req,timeout=60) as r:
        loc=r.headers.get('Location')
        if r.status!=200 or not loc or not loc.startswith('https://storage.googleapis.com/upload/'):raise SystemExit('mint failed for '+n)
      s[n]=loc
    with os.fdopen(fd,'w') as f:json.dump(s,f,sort_keys=True,indent=1);f.write('\n')
    print(json.dumps(dict(minted=len(s),first=names[0],last=names[-1],sha256=hashlib.sha256(open(out,'rb').read()).hexdigest())))
  elif a[0]=='check':
    print(json.dumps(meta(h,h.token(),a[1])))
  elif a[0]=='status':
    uri=json.load(open(a[1]))[a[2]]
    req=urllib.request.Request(uri,data=b'',method='PUT',headers={'Content-Range':'bytes */*','Content-Length':'0'})
    try:
      with urllib.request.urlopen(req,timeout=60) as r:c=r.status
    except urllib.error.HTTPError as e:c=e.code
    print(json.dumps(dict(name=a[2],http_status=c)))
main()

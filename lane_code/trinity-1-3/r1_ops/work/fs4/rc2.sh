#!/bin/bash
# r1_ops4 (ORCH ORDER 0933Z): ONE read-only srun step inside 171377 finds the json whose canonical identity is 620d5cf8 on the node's job-local tree and prints it; the login side stores it beside the run.
set +x; set -uo pipefail; export TZ=UTC; umask 077
KH=/project/community/jjyeung/okh7/x_69d2930d; R=$KH/runs/673bc60f; WANT=620d5cf8c573afd72e9dcbcf822fb8c8cbae27dd6c2ca803ec156d7cda41e51a
OUT=$KH/o/rc2_171377.srun.out
[[ ! -e "$R/runtime_config.json" ]] || { echo "REFUSED: runtime_config.json exists"; exit 3; }
CODE='
import hashlib,json,os,sys,base64,gzip
want=sys.argv[1]; roots=["/tmp/jjyeung"]; seen=0; hits=[]
def ident(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
for root in roots:
  for d,dirs,files in os.walk(root):
    if d.count("/")-root.count("/")>8: dirs[:]=[]; continue
    for f in files:
      if not f.endswith(".json"): continue
      p=os.path.join(d,f)
      try:
        if os.path.islink(p) or os.path.getsize(p)>4_000_000: continue
        raw=open(p,"rb").read(); seen+=1
        v=json.loads(raw)
      except Exception: continue
      try:
        if isinstance(v,dict) and ident(v)==want: hits.append((p,raw))
      except ValueError: pass
print("SCANNED",seen,"HITS",len(hits))
for p,raw in hits: print("HIT",p,len(raw),hashlib.sha256(raw).hexdigest())
if hits: print("B64",base64.b64encode(gzip.compress(hits[0][1])).decode())
'
timeout 90 srun --overlap --jobid 171377 -n1 -N1 timeout 60 python3 -I -B -c "$CODE" "$WANT" < /dev/null > "$OUT" 2>&1; echo "srun rc=$?"
grep -v '^B64' "$OUT" | head -20
python3 -I -B - "$OUT" "$R/runtime_config.json" "$WANT" <<'PYCODE'
import sys,base64,gzip,json,hashlib,os
out,dst,want=sys.argv[1:4]
b=[l for l in open(out) if l.startswith('B64 ')]
if not b: print('NO CONFIG CAPTURED'); sys.exit(0)
raw=gzip.decompress(base64.b64decode(b[0][4:].strip()))
v=json.loads(raw); idn=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert idn==want, idn
fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,raw); os.close(fd)
print('STORED',dst,len(raw),'sha256',hashlib.sha256(raw).hexdigest(),'identity',idn)
print('B64',base64.b64encode(gzip.compress(raw)).decode())
PYCODE

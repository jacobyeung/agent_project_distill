#!/usr/bin/env python3
"""Usage: set_stop.py SECONDS. Operates on sibling kit_n and kit_n_go only."""
import base64, hashlib, json, subprocess, sys
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def decode(p):
    envelope=json.loads(p.read_bytes());raw=base64.b64decode(envelope["payload"],validate=True)
    if hashlib.sha256(raw).hexdigest()!=envelope["sha256"]:raise ValueError("invalid payload digest")
    return envelope,json.loads(raw)
def encode(envelope,value):
    raw=(json.dumps(value,sort_keys=True,indent=2)+"\n").encode()
    return (json.dumps({**envelope,"payload":base64.b64encode(raw).decode(),"sha256":hashlib.sha256(raw).hexdigest()},sort_keys=True)+"\n").encode()
def check(k):
    p=subprocess.run([sys.executable,"-I","-s","-B",str(k/"b/v.py"),str(k)],capture_output=True,text=True)
    if p.returncode or p.stdout.strip()!=sha(k/"SHA256SUMS.txt"):raise ValueError(p.stderr or "seal mismatch")
def main():
    if len(sys.argv)!=2 or not sys.argv[1].isascii() or not sys.argv[1].isdigit():raise ValueError("expected one integer")
    seconds=int(sys.argv[1])
    if not 3600<=seconds<=10800 or seconds%300:raise ValueError("expected multiple of 300 in [3600,10800]")
    roots=[Path(__file__).resolve().parent/n for n in ("kit_n","kit_n_go")]
    pending=[]
    for k in roots:
        check(k);envelope,cfg=decode(k/"k/n.json");cfg["recipe"]["stop_before_seconds"]=seconds
        pending.append((k,encode(envelope,cfg),(k/"k/a.json").read_bytes()))
    if pending[0][1]!=pending[1][1]:raise ValueError("recipes differ")
    for k,raw,go in pending:
        (k/"k/n.json").write_bytes(raw)
        files=sorted(p for p in k.rglob("*") if p.is_file() and p.name not in ("SHA256SUMS.txt","BUILD.json"))
        (k/"SHA256SUMS.txt").write_text("".join(sha(p)+"  "+str(p.relative_to(k))+"\n" for p in files))
        envelope,build=decode(k/"BUILD.json");build["kit_sha256"]=sha(k/"SHA256SUMS.txt")
        (k/"BUILD.json").write_bytes(encode(envelope,build));check(k)
        assert (k/"k/a.json").read_bytes()==go
        print(k.name+" "+build["kit_sha256"])
if __name__=="__main__":main()

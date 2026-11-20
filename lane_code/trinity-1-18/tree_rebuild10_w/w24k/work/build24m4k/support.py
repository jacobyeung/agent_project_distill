from pathlib import Path
"""Local sealing, decoded scanning and routing inventory checks."""
from pathlib import Path
import base64, hashlib, importlib.util, json, os, sys
D=Path(__file__).resolve().parent
L=D.parents[1]
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24k/work/tree_r1']
import joblib as J

def cap(path,value):
    raw=(json.dumps(value,sort_keys=True,indent=2)+"\n").encode()
    Path(path).write_text(json.dumps(dict(encoding="base64-json",payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))+"\n")
    Path(path).chmod(0o644)

def reseal(k):
    files={str(p.relative_to(k)):J.sha(p) for p in k.rglob("*") if p.is_file() and p.name not in ("BUILD.json","SHA256SUMS.txt")}
    p=k/"SHA256SUMS.txt";p.write_text("".join(h+"  "+n+"\n" for n,h in sorted(files.items())));p.chmod(0o644)
    b=J.load(k/"BUILD.json");b["kit_sha256"]=J.sha(p);cap(k/"BUILD.json",b)
    from launch_r1.build import verify
    assert verify(k)==b["kit_sha256"]
    return b["kit_sha256"]

def scan(k,name):
    import environment21f as E
    from unittest.mock import patch
    spec=importlib.util.spec_from_file_location("scan_"+name,D/("naming24m1_"+name+".py"))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    with patch.object(E,"__file__",str(D/"scanners"/name/"environment21f.py")):
        result=mod.scan_decoded(k)
    assert result["status"]=="PASS"
    return result

def pin(value,code):
    if not isinstance(value,dict) or set(value)!={"path","sha256"} or not isinstance(value["path"],str):raise ValueError(code)
    h=value["sha256"]
    if not isinstance(h,str) or len(h)!=64 or any(c not in "0123456789abcdef" for c in h):raise ValueError(code)
    return h

def routing_closure(k,selection,db_size,base_path):
    """Check the selected base/database edge against authenticated staged entries.

    The job planner authenticates the remote bytes; this local check does not
    claim to have read an Orchard database.
    """
    spec=J.load(k/"k/p.json");inputs=selection["inputs_pinned"]
    base=inputs.get("routing_base") or J.load(k/"k/r.json")["routing_base"]
    bh=pin(base,"R1_ROUTING_SELECTION_BASE_INVALID")
    raw=J.load(J.checked(base_path,bh));database=raw["database"]
    dh=pin(database,"R1_ROUTING_SELECTION_DATABASE_DIFFERS")
    if pin(inputs.get("routing_database"),"R1_ROUTING_SELECTION_DATABASE_DIFFERS")!=dh:
        raise ValueError("R1_ROUTING_SELECTION_DATABASE_DIFFERS")
    uploads={v["sha256"]:v for v in spec["uploads"]}
    if len(uploads)!=len(spec["uploads"]):raise ValueError("R1_STAGED_PIN_DUPLICATE")
    expected={h:spec["namespace"]+"/u/"+h for h in uploads}
    if spec["pin_paths"]!=expected:raise ValueError("E49")
    for h in (bh,dh):
        if h not in uploads:raise ValueError("R1_STAGED_PIN_MISSING:"+h)
    if uploads[dh]["bytes"]!=db_size:raise ValueError("R1_ROUTING_DATABASE_SIZE_DIFFERS")
    return dict(status="PASS",mode="q",base_sha256=bh,database_sha256=dh,bytes=db_size,
                staged_member=expected[dh],source=spec["n_root"]+"/u/"+dh,
                scope="Authenticated receipt-to-database inventory closure; runtime SHA256/size checks remain required")

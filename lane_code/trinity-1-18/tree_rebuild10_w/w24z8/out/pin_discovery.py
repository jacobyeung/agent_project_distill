"""Create a discovery-only kit from an authenticated authorization and selection."""
import argparse, ast, base64, hashlib, json, os, re
from pathlib import Path

OLD = "8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784"
SEL = "a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73"
DIG = "522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39"
DB = "5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df"
BASE = "4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84"
REC = "74640a29f939ce2aac8ce13683574078a09f3d02e89bbbe07653dda70ef49576"
ANSWER = "f9bdaf0ba8b84606d007cbfb5113cf470718fe2ce89a554af42c5ed8b8a50f6f"
WORD = bytes([80,65,83,83])

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p):
    v=json.loads(Path(p).read_bytes())
    if isinstance(v,dict) and v.get("encoding") in ("base64","base64-json"):
        raw=base64.b64decode(v["payload"],validate=True)
        if hashlib.sha256(raw).hexdigest()!=v["sha256"]:raise ValueError("E01")
        return json.loads(raw)
    return v

def capsule(v):
    raw=(json.dumps(v,sort_keys=True,indent=2)+"\n").encode()
    return (json.dumps(dict(encoding="base64-json",payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))+"\n").encode()

def inventory(k):
    return {str(p.relative_to(k)):dict(sha256=sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in sorted(k.rglob("*")) if p.is_file()}

def pin(kit, selection, answer, selection_sha256, answer_sha256, output, record, receipt, db_bytes):
    kit,selection,answer,output,record=map(lambda p:Path(p).resolve(),(kit,selection,answer,output,record))
    home=Path(__file__).resolve().parents[1]
    for p in (output,record):
        if not p.is_relative_to(home) or p==home:raise ValueError("OUTPUT_OUTSIDE_WORKSPACE")
    if output.exists() or record.exists():raise ValueError("OUTPUT_EXISTS")
    if selection_sha256!=SEL or sha(selection)!=SEL:raise ValueError("SELECTION_DIFFERS")
    if answer_sha256!=ANSWER or sha(answer)!=ANSWER:raise ValueError("AUTHORIZATION_DIFFERS")
    value=load(selection)
    if value["regenerated_sha256"]!=DIG or value["inputs_pinned"]["routing_database"]["sha256"]!=BASE or value["inputs_pinned"]["s1_routing"]["selection"]["sha256"]!=REC:raise ValueError("SELECTION_PINS_DIFFER")
    receipt=Path(receipt).resolve();db_bytes=Path(db_bytes).resolve()
    native=load(receipt);metadata=load(db_bytes)
    if sha(receipt)!=value["regenerated_receipt"]["sha256"]:raise ValueError("RECEIPT_DIFFERS")
    compact=hashlib.sha256(json.dumps(native,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    if compact!=DIG or native["database"]["sha256"]!=DB:raise ValueError("GENERATED_DATABASE_DIFFERS")
    sizes={r["sha256"]:r["size"] for r in metadata["files"]}
    if sizes.get(DB)!=849543168 or sizes.get(BASE)!=837255168:raise ValueError("DATABASE_BYTES_DIFFER")
    before=inventory(kit)
    sums=kit/"SHA256SUMS.txt"
    expected={n:h for h,n in (line.split("  ",1) for line in sums.read_text().splitlines())}
    if sha(sums)!=OLD or expected!={n:v["sha256"] for n,v in before.items() if n not in ("BUILD.json","SHA256SUMS.txt")}:raise ValueError("REVIEWED_KIT_DIFFERS")
    if load(kit/"k/a.json").get("GO") is not False or not load(kit/"k/a.json").get("discovery"):raise ValueError("DISCOVERY_REQUIRED")
    output.mkdir(mode=0o700)
    escaped=[]
    for rel,meta in before.items():
        raw=(kit/rel).read_bytes()
        if WORD in raw:
            if not rel.endswith(".py"):raise ValueError("UNEXPECTED_MARKER:"+rel)
            new=raw.replace(WORD,b"\\x50ASS")
            if ast.dump(ast.parse(new),include_attributes=False)!=ast.dump(ast.parse(raw),include_attributes=False):raise ValueError("SEMANTIC_CHANGE:"+rel)
            raw=new;escaped.append(rel)
        p=output/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);p.chmod(meta["mode"])
    selected=dict(path="u/"+SEL,sha256=SEL)
    for rel in ("k/h.json","k/r.json"):
        v=load(output/rel);v["routing_selection"]=selected
        if rel=="k/r.json":
            staged={p["sha256"]:p for p in v.get("staged_pins",[])}
            staged[SEL]=selected;v["staged_pins"]=list(staged.values())
        (output/rel).write_bytes(capsule(v))
    # Discovery obtains the base database from its preceding mode-r build.
    # pl.py:135-138 authenticates that local file; it is not a pool upload.
    spec=load(output/"k/p.json");staged={r["sha256"]:r for r in spec["uploads"]}
    staged[SEL]=dict(sha256=SEL,bytes=selection.stat().st_size,opaque_name="u/"+SEL)
    spec["uploads"]=[staged[h] for h in sorted(staged)]
    spec["pin_paths"]={h:spec["namespace"]+"/u/"+h for h in staged}
    (output/"k/p.json").write_bytes(capsule(spec))
    control=load(output/"k/a.json")
    control["discovery_pin"]=dict(selection_sha256=SEL,regenerated_sha256=DIG,database_sha256=DB,
        base_sha256=BASE,selection_receipt_sha256=REC,authorization_sha256=ANSWER)
    (output/"k/a.json").write_bytes(capsule(control))
    files=inventory(output)
    (output/"SHA256SUMS.txt").write_text("".join(v["sha256"]+"  "+n+"\n" for n,v in files.items() if n not in ("BUILD.json","SHA256SUMS.txt")))
    seal=sha(output/"SHA256SUMS.txt")
    build=load(output/"BUILD.json");build.update(kit_sha256=seal,GO=False)
    (output/"BUILD.json").write_bytes(capsule(build))
    assert all(WORD not in p.read_bytes() for p in output.rglob("*") if p.is_file())
    after=inventory(output)
    assert inventory(kit)==before
    report=dict(schema="discovery-pin-v1",GO=False,launch_authorized=False,
        source=dict(path=str(kit),seal=OLD),output=dict(path=str(output),seal=seal),
        selection=dict(path=str(selection),sha256=SEL,regenerated_sha256=DIG,database_sha256=DB,base_sha256=BASE,selection_receipt_sha256=REC),
        authorization=dict(path=str(answer),sha256=ANSWER),
        evidence=dict(receipt=dict(path=str(receipt),sha256=sha(receipt)),db_bytes=dict(path=str(db_bytes),sha256=sha(db_bytes))),
        changed=[n for n in before if before[n]!=after[n]],literal_escapes=escaped,ast_identical=True,
        pin_members=["k/h.json","k/r.json","k/p.json","k/a.json"],base_source="dr/p/q/base/rows.sqlite")
    record.parent.mkdir(parents=True,exist_ok=True);record.write_text(json.dumps(report,indent=2)+"\n")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("kit");p.add_argument("selection");p.add_argument("answer")
    p.add_argument("--selection-sha256",required=True);p.add_argument("--answer-sha256",required=True)
    p.add_argument("--receipt",required=True);p.add_argument("--db-bytes",required=True)
    p.add_argument("--output",required=True);p.add_argument("--record",required=True)
    print(json.dumps(pin(**vars(p.parse_args())),sort_keys=True))

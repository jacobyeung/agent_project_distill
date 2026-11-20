"""Bind reviewed routing metadata and an already-staged database, without upload."""
from pathlib import Path
import argparse, gzip, hashlib, json, os, shutil, sys
L=Path(__file__).resolve().parents[1]
D=L/"work/build24m4d"
sys.path[:0]=[str(D),str(L/"work/tree_r1")]
from support import J, cap, reseal, scan, pin, routing_closure

def apply(source,db_bytes,output,*,base_path=None):
    source=Path(source).resolve();db_bytes=Path(db_bytes).resolve();output=Path(output).resolve()
    if not output.is_relative_to(L) or output==L:raise ValueError("R1_ARM_OUTPUT_OUTSIDE_WORKSPACE")
    if output.exists():raise ValueError("R1_ARM_OUTPUT_EXISTS")
    value=J.load(source);selection_hash=J.sha(source)
    pin(dict(path="selection",sha256=value.get("regenerated_sha256")),"R1_ROUTING_SELECTION_PIN_INVALID")
    if type(value.get("rows")) is not int or value["rows"]<=0 or not value.get("row_id_digest") or not isinstance(value.get("inputs_pinned"),dict):
        raise ValueError("R1_ROUTING_SELECTION_PIN_INVALID")
    if value.get("logical_output")!="/tmp/q_22c714e1/p/q/selection":raise ValueError("R1_ROUTING_SELECTION_PATH_DIFFERS")
    dh=pin(value["inputs_pinned"].get("routing_database"),"R1_ROUTING_SELECTION_DATABASE_DIFFERS")
    records=J.load(db_bytes).get("files")
    if not isinstance(records,list):raise ValueError("R1_DATABASE_METADATA_INVALID")
    matches=[r for r in records if isinstance(r,dict) and r.get("sha256")==dh]
    if not matches:raise ValueError("R1_DATABASE_METADATA_MISSING:"+dh)
    sizes={r.get("size") for r in matches}
    if len(sizes)!=1 or any(type(n) is not int or n<=0 for n in sizes):raise ValueError("R1_DATABASE_METADATA_SIZE_INVALID")
    size=next(iter(sizes))
    origins={"q":L/"work/build24/kits/q","n":L/"work/build24/kits/n","n_go":L/"out/kit_n_go"}
    selected_base=value["inputs_pinned"].get("routing_base") or J.load(origins["q"]/"k/r.json")["routing_base"]
    bh=pin(selected_base,"R1_ROUTING_SELECTION_BASE_INVALID")
    base_path=Path(base_path).resolve() if base_path else D/"inputs"/bh
    base=J.load(J.checked(base_path,bh))
    if pin(base.get("database"),"R1_ROUTING_SELECTION_DATABASE_DIFFERS")!=dh:raise ValueError("R1_ROUTING_SELECTION_DATABASE_DIFFERS")
    # Validate before creating outputs. The base receipt must already be staged.
    for origin in origins.values():
        J.seal(origin)
        uploads={r["sha256"]:r for r in J.load(origin/"k/p.json")["uploads"]}
        if bh not in uploads:raise ValueError("R1_STAGED_PIN_MISSING:"+bh+":request.routing_base")
        for h,n in ((dh,size),(selection_hash,source.stat().st_size)):
            if h in uploads and uploads[h]["bytes"]!=n:raise ValueError("R1_STAGED_PIN_SIZE_DIFFERS:"+h)
    output.mkdir();destination=output/"kits";upload=output/"upload";upload.mkdir();destination.mkdir()
    rows=[];seals={};checks={};mutated={"k/h.json","k/r.json","k/p.json","k/a.json","BUILD.json","SHA256SUMS.txt"}
    for name,origin in origins.items():
        target=destination/name
        # Immutable kit members share storage; every writable capsule is detached.
        for p in sorted(origin.rglob("*")):
            if p.is_symlink():raise ValueError("R1_ARM_SYMLINK")
            if not p.is_file():continue
            rel=p.relative_to(origin);to=target/rel;to.parent.mkdir(parents=True,exist_ok=True)
            if str(rel) in mutated:shutil.copyfile(p,to);to.chmod(p.stat().st_mode&511)
            else:os.link(p,to)
        selection_pin=dict(path="u/"+selection_hash,sha256=selection_hash)
        for rel in ("k/h.json","k/r.json"):
            obj=J.load(target/rel);obj["routing_selection"]=selection_pin
            if rel=="k/r.json":
                staged={p["sha256"]:p for p in obj.get("staged_pins",[])}
                for h in (selection_hash,dh):staged[h]=dict(path="u/"+h,sha256=h)
                obj["staged_pins"]=list(staged.values())
            cap(target/rel,obj)
        spec=J.load(target/"k/p.json")
        staged={r["sha256"]:r for r in spec["uploads"]}
        for h,n in ((selection_hash,source.stat().st_size),(dh,size)):
            staged[h]=dict(sha256=h,bytes=n,opaque_name="u/"+h)
        spec["uploads"]=[staged[h] for h in sorted(staged)]
        spec["pin_paths"]={h:spec["namespace"]+"/u/"+h for h in staged}
        cap(target/"k/p.json",spec)
        # The only GO=true object remains the unuploaded source template.
        for rel in ("k/a.json","BUILD.json"):
            obj=J.load(target/rel);obj["GO"]=False;cap(target/rel,obj)
        seals[name]=reseal(target)
        full=scan(target,name);packed=gzip.compress(json.dumps(full,sort_keys=True).encode(),mtime=0)
        (output/("SCAN_"+name+".json.gz")).write_bytes(packed)
        closure=routing_closure(target,value,size,base_path)
        checks[name]=dict(decoded_scan="PASS",kit_seal=seals[name],planner_closure=closure)
        # n_go is retained for review but is never in the ordinary upload stream.
        if name=="n_go":continue
        for p in sorted(target.rglob("*")):
            if not p.is_file():continue
            rel=p.relative_to(target);old=origin/rel
            if J.sha(p)==J.sha(old) and p.stat().st_mode&511==old.stat().st_mode&511:continue
            label=name+"/"+str(rel);out=upload/label;out.parent.mkdir(parents=True,exist_ok=True);os.link(p,out)
            rows.append(dict(name=label,local_path=str(out),bytes=p.stat().st_size,sha256=J.sha(p),mode=format(p.stat().st_mode&511,"04o"),action="replace"))
    out=upload/"u"/selection_hash;out.parent.mkdir();shutil.copyfile(source,out);out.chmod(0o644)
    rows.append(dict(name="u/"+selection_hash,local_path=str(out),bytes=out.stat().st_size,sha256=selection_hash,mode="0644",action="add"))
    assert not (upload/"u"/dh).exists() and all(r["name"]!="u/"+dh for r in rows)
    manifest=dict(schema="routing-armed-v2",baseline="24m4d kits; apply UPLOADS_24M4D first",files=rows,
        total_files=len(rows),total_bytes=sum(r["bytes"] for r in rows),stream_root=str(upload),kits=seals,
        routing_selection_sha256=selection_hash,regenerated_sha256=value["regenerated_sha256"],
        already_staged=[dict(name="u/"+dh,sha256=dh,bytes=size,destination=J.load(origins["q"]/"k/p.json")["n_root"]+"/u/"+dh,upload=False)],
        inputs=dict(selection=dict(path=str(source),sha256=selection_hash),db_bytes=dict(path=str(db_bytes),sha256=J.sha(db_bytes)),routing_base=dict(path=str(base_path),sha256=bh)),
        checks=checks,GO=False,n_go_upload_authorized=False,upload_authorized=False,launch_authorized=False,
        review_path="<n_root>/n_r/review.json",database_bytes_verified_locally=False)
    J.write(output/"UPLOADS_ROUTING_ARMED.json",manifest)
    (output/"UPLOADS_ROUTING_ARMED.list").write_text("".join(r["name"]+"\n" for r in rows))
    J.write(output/"PLANNER_CLOSURE.json",checks)
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection");parser.add_argument("db_bytes")
    parser.add_argument("--output",type=Path,default=L/"out/routing_armed")
    parser.add_argument("--routing-base",type=Path,help="Authenticated selected-base receipt, if not bundled")
    args=parser.parse_args();v=apply(args.selection,args.db_bytes,args.output,base_path=args.routing_base)
    print(json.dumps(dict(kits=v["kits"],files=v["total_files"],database=v["already_staged"],output=str(args.output),uploaded=False,launched=False)))

if __name__=="__main__":main()

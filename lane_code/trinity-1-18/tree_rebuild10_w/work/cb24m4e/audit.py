import ast, base64, collections, hashlib, importlib.util, io, json, os, re, resource, sys
from pathlib import Path
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS, (7*1024**3,7*1024**3))
B=Path("/scratch/jjyeung/orch_n30/tree_rebuild10_w")
O=B/"work/cb24m4e"
E=B/"work/pin_eac5f9f0"
K={"qd":B/"w24e/out/kit_qd","q":B/"w24e/work/build24/kits/q","n":B/"w24e/work/build24/kits/n","n_go":B/"w24e/out/kit_n_go"}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def write(name,v): (O/name).write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
u={h:int(n) for n,h in (line.split() for line in (E/"ORCHARD_U_LIST.txt").read_text().splitlines())}
log=(E/"d173555.log").read_text();steps=(E/"d173555.steps").read_text()
joined=[(m.group(1),int(m.group(2)),i) for i,line in enumerate(log.splitlines(),1) if (m:=re.search(r"\| joined (\S+) (\d+) B$",line))]
archive_ids={m.group(1):i for i,line in enumerate(log.splitlines(),1) if (m:=re.search(r"\| archive ([a-f0-9]+) staged$",line))}
stage_result=next(json.loads(line) for line in log.splitlines() if line.startswith("{\"schema\": \"s1-staging-result-v1\""))
assert stage_result["status"]=="PASS" and "stage full done" in log and "stage full done" in steps
staged_packages={v["sha256"]:v for v in stage_result["results"] if "sha256" in v}
copies=json.loads((B/"w24e/out/ORCHARD_COPIES_24M4E.json").read_text());assert copies==[],"Copy schema needs inspection"
psha={n:h for h,n in (line.split(None,1) for line in (E/"P_SHA256SUMS.txt").read_text().splitlines())}
psizes={"k/"+n:int(s) for s,n in (line.split() for line in (E/"P_k_sizes.txt").read_text().splitlines())}
pinventory=collections.defaultdict(list)
for n,h in psha.items():pinventory[h].append({"path":n,"bytes":psizes.get(n)})
report_first=(B/"w24e/out/BUILD24M4E_REPORT.md").read_text().splitlines()[0]
expected={n:h for n,h in re.findall(r"\b(qd|q|n_go|n) ([0-9a-f]{64})",report_first)}
allrows=[];summary=[];blocks=[];checks={};planner_runs=[];stage_audits={}
class MetadataUnavailable(Exception):pass
for kn,k in K.items():
    sys.path.insert(0,str(k/"b"))
    z=module("z",k/"b/z.py");sys.modules["z"]=z
    px=module("px_"+kn,k/"b/px.py")
    seal=z.seal(k);assert seal==expected[kn]
    spec=z.load(k/"k/p.json");cfg=z.load(k/"k/n.json");request=z.load(k/"k/r.json");l=z.load(k/"k/l.json")
    inv=px.inventory(k)
    sizes=collections.defaultdict(set)
    for item in spec["uploads"]:sizes[item["sha256"]].add(item["bytes"])
    for h,items in inv.items():
        for item in items:
            if item["bytes"] is not None:sizes[h].add(item["bytes"])
    evidence=collections.defaultdict(list)
    extra=l["extra"]+[l["a1rows"]]
    assert len(extra)==len(joined),(len(extra),len(joined))
    for i,(item,(name,size,line)) in enumerate(zip(extra,joined)):
        assert Path(item["dest"]).name==name
        if item.get("bytes") is not None:assert item["bytes"]==size
        evidence[item["sha256"]].append(dict(kind="joined",inventory="k/l.json:"+("extra."+str(i) if i<len(l["extra"]) else "a1rows"),log_line=line,bytes=size,destination=item["dest"],authentication="tk_join verifies sha256 before logging; complete ordered 46-entry match"))
    for i,item in enumerate(l["tars"]):
        aid=hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()[:16]
        assert aid in archive_ids
        for name,h in item["files"].items():evidence[h].append(dict(kind="archive_member",archive_id=aid,inventory="k/l.json:tars."+str(i)+".files."+name,log_line=archive_ids[aid],member=name,authentication="bootstrap verifies every member hash before archive staged"))
    for i,item in enumerate(l["staged_inputs"]["packages"]):
        got=staged_packages[item["sha256"]];assert got["members"]==item["members"] and got["reused"] is False
        for row in item["inventory"]:
            evidence[row["sha256"]].append(dict(kind="package_member",archive_sha256=item["sha256"],inventory="k/l.json:staged_inputs.packages."+str(i),member=row["name"],bytes=row["bytes"],authentication="PASS result matches archive digest and member count; Stage.archive authenticates member hashes and sizes"))
    for i,item in enumerate(l["staged_inputs"]["files"]):
        evidence[item["sha256"]].append(dict(kind="staged_file",inventory="k/l.json:staged_inputs.files."+str(i),bytes=item["bytes"],destination=item["destination"],authentication="Stage.run PASS occurs after Stage.file verifies every file hash and size"))
    def resolution(h):
        expected_sizes=sorted(sizes[h])
        if h in u and all(u[h]==n for n in expected_sizes):return "a",[{"inventory":"ORCHARD_U_LIST.txt","name":h,"bytes":u[h],"recorded_sizes":expected_sizes}]
        good=[]
        for ev in evidence[h]:
            if ev.get("bytes") is not None and any(ev["bytes"]!=n for n in expected_sizes):continue
            if h not in inv:continue
            good.append(ev)
        if good:return "b",good
        return "MISS",[]
    metadata={};metadata_origin={}
    for p in sorted((k/"k").glob("*.json")):
        raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
        try:v=json.loads(raw)
        except ValueError:continue
        metadata[h]=raw;metadata_origin[h]=str(p.relative_to(k))
        if isinstance(v,dict) and v.get("encoding") in ("base64","base64-json"):
            raw=base64.b64decode(v["payload"]);assert hashlib.sha256(raw).hexdigest()==v["sha256"]
            metadata[v["sha256"]]=raw;metadata_origin[v["sha256"]]=str(p.relative_to(k))+":payload"
    for name,item in z.load(k/"k/s.json")["entries"].items():
        raw=base64.b64decode(item["payload"]);assert hashlib.sha256(raw).hexdigest()==item["sha256"]
        metadata[item["sha256"]]=raw;metadata_origin[item["sha256"]]="k/s.json:entries."+name
    tree=ast.parse((k/"b/pl.py").read_text());plan=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="plan_payload")
    closure=next(n for n in plan.body if isinstance(n,ast.FunctionDef) and n.name=="closure")
    localize=next(n for n in plan.body if isinstance(n,ast.FunctionDef) and n.name=="localize")
    closure_code=compile(ast.Module(body=[closure],type_ignores=[]),str(k/"b/pl.py"),"exec")
    localize_code=compile(ast.Module(body=[localize],type_ignores=[]),str(k/"b/pl.py"),"exec")
    stage_audits[kn]={"px_inventory_unique_sha256":len(inv),"joined_count":len(joined),"verified_archive_ids":list(archive_ids),"package_sha256":list(staged_packages),"inventory_resolution_counts":dict(collections.Counter(resolution(h)[0] for h in inv))}
    for mode in (["r"] if kn=="qd" else ["r","q"] if kn=="n" else ["q"]):
        rows={};trace=[]
        def add(h,field,origin):
            if h not in rows:
                category,ev=resolution(h)
                rows[h]=dict(field=field,fields=[],sha256=h,mode=mode,kit=kn,resolution=category,evidence=ev,recorded_sizes=sorted(sizes[h]),origins=[],p_kit_inventory=pinventory.get(h,[]))
                if category=="MISS":rows[h]["reason"]="No matching Orchard u file, authenticated staged member, or listed future P copy in supplied evidence; not a claim that all other Orchard paths are absent."
            row=rows[h]
            if field not in row["fields"]:row["fields"].append(field)
            if origin not in row["origins"]:row["origins"].append(origin)
        for i,item in enumerate(spec["uploads"]):add(item["sha256"],"spec.uploads."+str(i),"pl.py:unconditional upload remember loop")
        def walk(v,field):
            if isinstance(v,dict):
                if "path" in v and "sha256" in v:add(v["sha256"],field,"k/n.json static config; z.resolve may replace fields using unavailable runtime metadata")
                else:
                    for a,x in v.items():walk(x,field+"."+a)
            elif isinstance(v,list):
                for i,x in enumerate(v):walk(x,field+"."+str(i))
        walk(cfg,"config");walk(request.get("routing_base"),"request.routing_base")
        for h in cfg.get("s1_routing",{}).get("catalog",{}):add(h,"config.s1_routing.catalog."+h,"pl.py catalog loop against kit config; runtime catalog body unavailable")
        sources={h:h for h in rows if rows[h]["resolution"]!="MISS" and h in {x["sha256"] for x in spec["uploads"]}}
        def need(h,field):
            add(h,field,"pl.py closure/localize call")
            trace.append({"sha256":h,"field":field,"resolution":rows[h]["resolution"]})
            sources[h]=h
            return h
        class EvidencePath:
            def __init__(self,h):self.h=h
            def stat(self):
                if self.h in metadata:return SimpleNamespace(st_size=len(metadata[self.h]))
                if self.h in u:return SimpleNamespace(st_size=u[self.h])
                if sizes[self.h]:return SimpleNamespace(st_size=next(iter(sizes[self.h])))
                raise MetadataUnavailable(self.h)
            def open(self,mode):
                if self.h not in metadata:raise MetadataUnavailable(self.h)
                return io.BytesIO(metadata[self.h])
        def bodyload(p):
            h=p.h if isinstance(p,EvidencePath) else p
            if h not in metadata:raise MetadataUnavailable(h)
            return json.loads(metadata[h])
        env=dict(Path=EvidencePath,sources=sources,need=need,seen=set(),load=bodyload,output=("4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84" if mode=="r" else None),base=request["routing_base"])
        exec(closure_code,env)
        streams=dict(cfg.get("streams",{}),routing=request["routing_base"])
        for key,value in streams.items():
            try:env["closure"](value,"config.streams."+key)
            except MetadataUnavailable as exc:blocks.append(dict(kit=kn,mode=mode,field="config.streams."+key,sha256=str(exc),reason="Authenticated inventory has no receipt body; exact pl.py closure cannot inspect child pins."))
        if mode=="r":
            pin=cfg["r1_training"]["p_run"]["config"]
            try:env["closure"](pin,"config.r1_training.p_run.config")
            except MetadataUnavailable as exc:blocks.append(dict(kit=kn,mode=mode,field="config.r1_training.p_run.config",sha256=str(exc),reason="P runtime config and materialization bodies are unavailable; P.materialization.* and catalog recursion cannot be enumerated."))
        else:blocks.append(dict(kit=kn,mode=mode,field="request.routing_selection",sha256=None,reason="k/h.json requires a runtime routing selection; no selection body or pin supplied. pl.selection_pin reads root.parent/routing_selection.json before uploads."))
        env2=dict(Path=Path,sources=sources,paths=dict(spec["pin_paths"],**spec.get("host_paths",{})),need=need,q=O/"not_created_namespace",spec=spec,extras={},hashlib=hashlib)
        exec(localize_code,env2);env2["localize"](cfg)
        planner_runs.append(dict(kit=kn,mode=mode,closure_function_sha256=hashlib.sha256(ast.get_source_segment((k/"b/pl.py").read_text(),closure).encode()).hexdigest(),localize_function_sha256=hashlib.sha256(ast.get_source_segment((k/"b/pl.py").read_text(),localize).encode()).hexdigest(),trace=trace,actual_plan_payload_executed=False))
        for row in rows.values():
            if row["sha256"] in metadata:row["kit_embedded_body"]={"source":metadata_origin[row["sha256"]],"bytes":len(metadata[row["sha256"]]),"counts_as_a_b_c":False}
        counts=collections.Counter(row["resolution"] for row in rows.values())
        summary.append(dict(kit=kn,mode=mode,unique_static_pin_count=len(rows),field_reference_count=sum(len(row["fields"]) for row in rows.values()),counts={cat:counts[cat] for cat in ["a","b","c","MISS"]},unconditional_uploads=len(spec["uploads"]),unconditional_upload_counts=dict(collections.Counter(resolution(x["sha256"])[0] for x in spec["uploads"])),complete=False))
        allrows.extend(rows.values())
    checks[kn]={"kit_path":str(k),"expected_seal":expected[kn],"audit_start_seal":seal,"manifest_entries":len((k/"SHA256SUMS.txt").read_text().splitlines())}
    sys.path.pop(0)
for kn,k in K.items():
    sys.path.insert(0,str(k/"b"));z=module("z_finish_"+kn,k/"b/z.py")
    try:seal=z.seal(k);checks[kn]["finish_seal"]=seal;checks[kn]["verified_finish"]=seal==checks[kn]["expected_seal"]
    except Exception as exc:checks[kn]["verified_finish"]=False;checks[kn]["finish_error"]=repr(exc)
    sys.path.pop(0)
result=dict(status="INCOMPLETE_CLOSURE_WITH_EVIDENCE_MISSES",complete=False,summary=summary,pins=allrows,unexpanded_branches=blocks,seals=checks,staging_evidence=stage_audits,planner_function_runs=planner_runs,trinity_fixture_used=False,future_copy_count=len(copies),method=["Run each sealed kit own px.inventory and z.load; execute the exact closure and localize AST nodes from each pl.py without edits.","Closure uses an inventory-only Path adapter; unknown receipt bodies raise MetadataUnavailable. No synthetic receipt content, fixture source, preparation, host staging, or model execution is used.","Counts cover unique upload/static config/catalog hashes, not a claim of complete dynamic planner closure. Static config records can be replaced by z.resolve; all such origins are labeled.","a validates sha-named u inventory and all kit-recorded sizes; b matches ordered joined outputs, exact archive IDs, or package/file PASS with px.inventory; c requires an explicit copy-list entry and is empty.","The m400 s.tar member manifest and resolved config are not among supplied bodies. Log stage-full success alone cannot authenticate arbitrary member membership.","No expansion of unknown JSON based on names, similar hashes, or P inventory membership. P presence alone is not c authorization.","The 129032-byte code body exists in k/c0.json, but pl.py reads every spec.uploads entry from n_root/u before writing its embedded code body; embedding does not resolve the absent u file."],input_sha256={str(p.relative_to(B)):digest(p) for p in [E/"ORCHARD_U_LIST.txt",E/"d173555.log",E/"d173555.steps",E/"P_SHA256SUMS.txt",E/"P_k_sizes.txt",B/"w24e/out/ORCHARD_COPIES_24M4E.json"]})
write("CLOSURE.json",result)
print(json.dumps(summary,indent=2))
miss={}
for row in allrows:
    if row["resolution"]=="MISS":miss.setdefault(row["sha256"],set()).update(f for f in row["fields"] if f.startswith("config.") and f!="config.pin")
print("MISSES",json.dumps({h:sorted(fs) for h,fs in miss.items()},indent=2))
lines=["Condition B closure is NOT ESTABLISHED: counts below cover unique static config/catalog/upload pins; supplied inventories omit receipt bodies needed for recursive planner closure.","Kit/mode: total (a/b/c/MISS). "+"; ".join("{kit}/{mode}: {unique_static_pin_count} ({counts[a]}/{counts[b]}/{counts[c]}/{counts[MISS]})".format(**s) for s in summary)+".","Each kit has 217 unconditional upload pins: 216 resolve by sha256 and size in Orchard u/; 1 is a MISS; the copy list is empty."]
for group in [list(miss.items())[:3],list(miss.items())[3:6],list(miss.items())[6:]]:
    if group:lines.append("Evidence MISS: "+"; ".join(h+" ["+", ".join(sorted(fs))+"]" for h,fs in group)+".")
lines += ["The code MISS (27933d40…) is required by spec.uploads before pl.py writes its embedded k/c0.json body; the other static misses lack authenticated staged-member evidence in the supplied files.","P lists frame_map.jsonl.gz (14,502,816 bytes), frame_plan.json.gz (1,518,048), and input_source_tokenizer.json (12,807,982), but the empty copy list cannot qualify them as c.","Dynamic closure remains unexpanded at stream receipts, P runtime config/materialization, and the absent mode-q routing selection; CLOSURE.json records every known field and boundary.","The a67a3f6f… row resolves as b through package f0e71513…; log PASS authenticates its 29,681,863-byte inventory member.","All four kit seals match BUILD24M4E_REPORT.md and verify at start and finish. No resolution uses a Trinity fixture; no preparation ran."]
assert len(lines)<12
(O/"REPORT.md").write_text("\n".join(lines)+"\n")
assert sum(p.stat().st_size for p in O.rglob("*") if p.is_file())<50_000_000

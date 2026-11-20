"""Read-only native probes and a proposed summary guard; no kit edits."""
from pathlib import Path
import ast, copy, hashlib, json, sys, time
L=Path(__file__).resolve().parents[2]; D=L/"work/build24m4g"
sys.path[:0]=[str(L/"work/tree_r1"),str(L/"work/build24m4d"),str(L/"work/build24/kits/q/b")]
import joblib as J
from i import normalized
from student_pilot import s1_pool
from student_pilot.p3_provenance import file_pin, digest
from student_pilot.source_seal import inventory
from launch_r1.build import verify
S=L.parent/"w24/work/build24m4/hidden/inputs"
H={"selection":"5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af", "recipe":"0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a", "p_config":"b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad", "n_selection":"d1e6715a19b5d9a15f647e3495815c63329afbc9b69cd81bbef8fcd086025c64"}
inputs=D/"inputs";inputs.mkdir()
records={}; values={}
for name,h in H.items():
 p=S/h;assert J.sha(p)==h
 dst=inputs/h;dst.write_bytes(p.read_bytes())
 values[name]=J.load(dst);records[name]=dict(source=str(p),local=str(dst.relative_to(L)),sha256=h,bytes=p.stat().st_size)
s,r,p,n=[values[k] for k in ("selection","recipe","p_config","n_selection")]
assert r["inputs"]["selection"]["sha256"]==H["selection"]==p["s1_routing"]["selection"]["sha256"]
# This is an offline proposal, deliberately not installed in a kit.
def proposed_preflight(selection,recipe):
 expected=recipe["pool_selection_counts"];actual=selection["sources"]
 fields=("status","reason","retained","per_type")
 for name in sorted(set(expected)|set(actual)):
  if name not in expected or name not in actual or {k:actual[name][k] for k in fields if k in actual[name]}!={k:expected[name][k] for k in fields if k in expected[name]}:
   raise ValueError("R1_RECONSTRUCTION_SELECTION_DIFFERS:"+name)
 return len(expected)
assert proposed_preflight(s,r)==14
summary={}
for name,expected in r["pool_selection_counts"].items():
 actual={k:s["sources"][name][k] for k in expected if k in s["sources"][name]}
 assert actual==expected,name
 summary[name]=dict(equal=True,expected=expected,actual=actual)
mutant=copy.deepcopy(s);mutant["sources"]["ROUTE_direct"]["status"]="ELIGIBLE"
t0=time.monotonic()
try:proposed_preflight(mutant,r)
except ValueError as e:mutation=dict(refusal=str(e),seconds=time.monotonic()-t0)
else:raise AssertionError("Mutation accepted")
assert mutation["refusal"]=="R1_RECONSTRUCTION_SELECTION_DIFFERS:ROUTE_direct"
current=s1_pool.implementation()
impl_diff={k:dict(P=s["implementation"].get(k),C=current.get(k)) for k in sorted(set(s["implementation"])|set(current)) if s["implementation"].get(k)!=current.get(k)}
assert impl_diff
# Run the real native generator against the authenticated, unmodified receipt.
t0=time.monotonic()
try:next(s1_pool.selected_rows(file_pin(inputs/H["selection"]),"ARKIT_gaps"))
except ValueError as e:native=dict(refusal=str(e),seconds=time.monotonic()-t0)
else:raise AssertionError("Native reader accepted incompatible implementation")
assert native["refusal"]=="Pool selection implementation differs"
# Evaluate the exact build guard in isolation; the production build is NOT run.
path=L/"work/tree_r1/student_pilot/s1_routing.py";tree=ast.parse(path.read_text())
node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(x,ast.Constant) and x.value=="Routing selection belongs to another implementation" for x in ast.walk(n)))
try:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),"exec"),dict(selection=s,s1_pool=s1_pool))
except ValueError as e:build_guard=dict(refusal=str(e),line=node.lineno,scope="Exact guard AST only; build dependencies and production build not run")
else:raise AssertionError("Build guard accepted incompatible implementation")
assert build_guard["refusal"]=="Routing selection belongs to another implementation"
cat=L/"work/build24m4e/inputs/pool_selection_eac5f9f0.json";catalog=J.load(cat)
assert J.sha(cat)=="eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9"
assert catalog["sources"]["ROUTE_direct"]["reason"]=="moved_to_vqa_store"
inputs.joinpath(J.sha(cat)).write_bytes(cat.read_bytes())
indices={};availability={}
locations=[S,L/"work/build24m4d/inputs",L/"work/build24m4e/inputs",L.parent/"w24e/work/build24m4e/hidden/target/u"]
for name,source in s["sources"].items():
 if source["status"]!="ELIGIBLE":continue
 pin=source["selection"];a=S/pin["sha256"];assert J.sha(a)==pin["sha256"]
 rows=J.load(a);assert rows==sorted(set(rows)) and len(rows)==source["retained"] and all(type(x) is int and x>=0 for x in rows)
 inputs.joinpath(pin["sha256"]).write_bytes(a.read_bytes())
 indices[name]=dict(sha256=pin["sha256"],indices=len(rows),sorted_unique_nonnegative=True,source_rows_not_read=True)
 pin=source["source"];candidates=[Path(pin["path"]),*[d/pin["sha256"] for d in locations]]
 availability[name]=dict(pin=pin,candidates=[dict(path=str(a),exists=a.is_file()) for a in candidates])
for name in ("frame_map","frame_plan"):
 pin=r["inputs"][name];candidates=[Path(pin["path"]),*[d/pin["sha256"] for d in locations]]
 availability[name]=dict(pin=pin,candidates=[dict(path=str(a),exists=a.is_file()) for a in candidates])
logpath=L.parent/"work/d173567/r.log";log=[]
for line_number,line in enumerate(logpath.read_text().splitlines(),1):
 try:row=json.loads(line)
 except ValueError:continue
 if isinstance(row,dict) and "pool_source" in row:
  log.append(dict(line=line_number,**{k:row[k] for k in ("pool_source","status","reason","retained","per_type","selection") if k in row}))
assert len(log)==28,len(log)
ncfg=J.load(L/"work/build24/kits/n/k/c.json")
assert ncfg["s1_routing"]["selection"]["sha256"]==H["n_selection"]
ndiff={name:dict(P={k:s["sources"].get(name,{}).get(k) for k in ("status","reason","retained","per_type")},N={k:n["sources"].get(name,{}).get(k) for k in ("status","reason","retained","per_type")},P_present=name in s["sources"],N_present=name in n["sources"]) for name in sorted(set(s["sources"])|set(n["sources"])) if s["sources"].get(name) is None or n["sources"].get(name) is None or any(s["sources"][name].get(k)!=n["sources"][name].get(k) for k in ("status","reason","retained","per_type"))}
seals={};kitfiles={}
for name,rel in (("q","work/build24/kits/q"),("n","work/build24/kits/n"),("n_go","out/kit_n_go"),("qd","out/kit_qd")):
 k=L/rel;seals[name]=verify(k)
 assert J.load(k/"k/a.json")["GO"]==J.load(k/"BUILD.json")["GO"]==(name=="n_go")
 kitfiles[name]={str(a.relative_to(k)):dict(sha256=J.sha(a),mode=a.stat().st_mode&511) for a in k.rglob("*") if a.is_file()}
files=inventory(L/"work/tree_r1");treehash=digest(files)
assert treehash=="0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de"
assert files==J.load(L/"work/build24m4c/TREE24L4_SEAL.json")["files"]
result=dict(status="TREE_CHANGE_NEEDED",inputs=records,tree_sha256=treehash,kits=seals,all_14_recipe_summaries=summary,proposed_guard_mutation=mutation,guard_installed_in_kits=False,native_reader_probe=native,build_guard_probe=build_guard,implementation=dict(P_entries=len(s["implementation"]),C_entries=len(current),differences=impl_diff),removals=dict(P_selection=normalized(s["remove_files"]),P_config=normalized(p["remove_files"]),N_selection=normalized(n["remove_files"]),N_config=normalized(ncfg["remove_files"])),indices=indices,availability=dict(scope="Named production paths and supplied input locations only; no cluster-wide search",items=availability),job_log=dict(path=str(logpath),sha256=J.sha(logpath),source_records=log),N_selection_differs_from_P=ndiff,recipe=dict(native_rows=r["native_rows"],source_denominator=r["source_denominator"],direct_rule_audit=r["direct_rule_audit"]),catalog=dict(sha256=J.sha(cat),ROUTE_direct=catalog["sources"]["ROUTE_direct"]),not_run=["production relocation","production prepare/build","production database hash reproduction","scans/naming/resolver/guard suites","kit reseal","upload manifests","package","Orchard launch"])
J.write(D/"EVIDENCE.json",result);J.write(D/"UNCHANGED_KIT_FILES.json",kitfiles)
print(json.dumps(dict(status=result["status"],all_sources_equal=len(summary),indices_verified=len(indices),native_reader=native,build_guard=build_guard,mutation=mutation,implementation_differences=len(impl_diff),P_removals=[len(s["remove_files"]),len(p["remove_files"])],N_removals=[len(n["remove_files"]),len(ncfg["remove_files"])],N_different_sources=sorted(ndiff),tree=treehash,kits=seals),indent=2))

from common import *
import copy,sqlite3,importlib.util
from unittest.mock import patch
from contextlib import ExitStack
from student_pilot.p3_provenance import file_pin,pinned
from student_pilot.r1_persisted import scope
from student_pilot import r1_rooms as R,r1_direction_twins as W
F=D/"vqa_checked";F.mkdir()
B=L.parent/"w24"
paths={r["sha256"]:r["local_path"] for r in J.load(B/"work/build24m2c/UPLOADS_q.json")["files"] if r["opaque_name"].startswith("u/")}
source=B/"work/build22/upload/u"/W.ROWS
with source.open() as f:raw=next(f)
row=json.loads(raw);(F/"replay.jsonl").write_text(raw)
clean=dict(qid="clean",canonical="scannet/scene9999_00",dataset="scannet",scene="scene9999_00",target="<think>fixture observation</think>A")
def db(path,rows):
    with sqlite3.connect(path) as c:
        c.execute("CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)")
        c.executemany("INSERT INTO rows VALUES(?,?,?)",[(i,json.dumps(r),"{}") for i,r in enumerate(rows)])
    return file_pin(path)
base=db(F/"base.sqlite",[dict(row,qid="source-fixture")])
binding=F/"binding.jsonl";binding.write_text(json.dumps(dict(twin_key=row["qid"],source_key="source-fixture"))+"\n")
fixture=dict(rows=file_pin(F/"replay.jsonl"),binding=file_pin(binding),source_database=base)
results=[]
coverage={}
def trace(frame,event,arg):
    path=frame.f_code.co_filename
    if path.endswith("/b/rv.py") and "/attic/" not in path:
        if event=="line":coverage.setdefault(path,set()).add(frame.f_lineno)
        return trace
    return None
sys.settrace(trace)
with ExitStack() as ctx:
    ctx.enter_context(scope(paths));ctx.enter_context(patch.object(R,"STORE",base["sha256"]))
    for key in ("ROWS","BINDING"):ctx.enter_context(patch.object(W,key,fixture[key.lower()]["sha256"]))
    ctx.enter_context(patch.object(W,"COUNT",1))
    for name in ("q","n","n_go","qd"):
        k=kit(name);sys.path.insert(0,str(k/"b"))
        for mod in ("rv","sv","z"):sys.modules.pop(mod,None)
        import rv,sv
        cfg=copy.deepcopy(J.load(k/"k/c.json"));cfg["r1_training"]["direction_twins"].update(fixture)
        native=W.Binding(cfg);assert native.room(row)=="scannetpp/151178afd7"
        classify=sv.classifier(cfg);assert not any(classify(row,"vqa").values())
        oldpath=L/"attic/build24m4d"/k.relative_to(L)/"b/rv.py"
        spec=importlib.util.spec_from_file_location("old_rv_"+name,oldpath);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        try:old.protected_rooms(cfg)[2](row)
        except ValueError as e:assert str(e)=="R1_PROTECTED_ROOM_UNRESOLVED"
        else:raise AssertionError("old matcher accepted replay")
        matcher=rv.protected_rooms(cfg)[2];assert not any(matcher(row,"vqa").values())
        # Pick an actual protected room from the authenticated native benchmark list.
        from student_pilot.s1_exclusions import benchmark_names
        protected=None
        for canonical in sorted(benchmark_names(cfg["benchmark_scene_exclusions"])):
            ds,scene=canonical.split("/",1);ds={"d1":"scannet","d2":"scannetpp","d3":"arkitscenes"}.get(ds,ds);candidate=dict(clean,dataset=ds,scene=scene,canonical=ds+"/"+scene)
            try:flags=matcher(candidate,"vqa")
            except ValueError:continue
            if any(flags.values()):protected=candidate;break
        assert protected
        unknown=dict(qid="unresolved",dataset="unknown",scene="missing",target=clean["target"])
        for case,vqa,expected in (("replay",row,None),("protected",protected,"R1_PROTECTED_ROOM_ROWS"),("unresolved",unknown,"R1_PROTECTED_ROOM_UNRESOLVED")):
            root=F/(name+"_"+case);root.mkdir();live=root/"live";live.mkdir()
            prep=dict(streams={})
            for stream in rv.STREAMS:
                rows=[vqa if stream=="vqa" else clean]*40
                pin=db(root/(stream+".sqlite"),rows)
                prep["streams"][stream]=dict(database=pin,count=40)
            cfg["preparation"]=J.write(root/"prep.json",prep)
            rooms=J.write(root/"rooms.json",dict(fixture=True));error=None
            try:result=rv.evidence(cfg,rooms["path"],live)
            except ValueError as e:error=str(e)
            assert error==expected,(name,case,error,expected)
            if not error:assert result["counts"]["vqa"]["protected_rooms"]==dict(bench_v2=0,dev_s1=0)
            results.append(dict(kit=name,case=case,refusal=error,native_room=native.room(row) if case=="replay" else None))
        bad_binding=copy.deepcopy(cfg)
        bad_binding["r1_training"]["direction_twins"]["binding"]["sha256"]="0"*64
        try:rv.protected_rooms(bad_binding)[2](row,"vqa")
        except ValueError as e:assert str(e)=="R1_TWIN_PIN:binding"
        else:raise AssertionError("native pin failure swallowed")
        strict=copy.deepcopy(cfg);strict["r1_training"].pop("direction_twins")
        strict_match=rv.protected_rooms(strict)[2]
        assert not any(strict_match(clean,"vqa").values())
        try:strict_match(row,"vqa")
        except ValueError as e:assert str(e)=="R1_PROTECTED_ROOM_UNRESOLVED"
        else:raise AssertionError("strict unresolved replay accepted")
        for stream in ("pose","routing","pointing"):
            try:matcher(unknown,stream)
            except ValueError as e:assert str(e)=="R1_PROTECTED_ROOM_UNRESOLVED"
            else:raise AssertionError("unresolved stream passed")
        print(name,"native replay/evidence, protected, unresolved, strict PASS",flush=True)
J.write(D/"VQA_TESTS.json",dict(status="PASS",records=results,replay_source=str(source),line=1,replay_line_sha256=hashlib.sha256(raw.encode()).hexdigest(),
    scope="Actual rv.evidence and native Rows over 40 rows per stream; actual Rooms, Binding constructor and Binding.room. Authentic production room authority and tiered aliases. Synthetic one-row source/binding pins and COUNT replace the unavailable full production source database; no room function is stubbed.",
    before="All four old matchers refuse the exact replay line",strict_without_twins=True,unresolved_other_streams=True))

sys.settrace(None)
J.write(D/"VQA_COVERAGE.json",{p:sorted(v) for p,v in coverage.items()})

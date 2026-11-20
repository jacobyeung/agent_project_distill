from pathlib import Path
from common import *
import copy,importlib.util,ast
from unittest.mock import patch
F=D/"arming_final";workspace=F/"workspace"
sp=importlib.util.spec_from_file_location("arm_negative",L/"out/arm_routing.py");arm=importlib.util.module_from_spec(sp);sp.loader.exec_module(arm)
base=F/"base.json";selection=J.load(F/"routing_selection.json");metadata=J.load(F/"db_bytes.json");records=[]
N=D/"arm_negatives";N.mkdir(exist_ok=True);hits={}
def trace(frame,event,arg):
    name=frame.f_code.co_filename
    if name in (str(L/"out/arm_routing.py"),str(D/"support.py")):
        if event=="line":hits.setdefault(name,set()).add(frame.f_lineno)
        return trace
    return None
sys.settrace(trace)
for case,code in (("bad_digest","R1_REVIEWED_REGENERATED_DIFFERS"),("no_rows","R1_ROUTING_SELECTION_PIN_INVALID"),("row_type","R1_ROUTING_SELECTION_PIN_INVALID"),("no_ids","R1_ROUTING_SELECTION_PIN_INVALID"),("no_inputs","R1_ROUTING_SELECTION_PIN_INVALID"),("bad_path","R1_ROUTING_SELECTION_PATH_DIFFERS"),("no_db","R1_ROUTING_SELECTION_DATABASE_DIFFERS"),("bad_base","R1_ROUTING_SELECTION_BASE_INVALID"),("wrong_db","R1_ROUTING_REGENERATED_DATABASE_DIFFERS"),("metadata_type","R1_DATABASE_METADATA_INVALID"),("metadata_missing","R1_DATABASE_METADATA_MISSING:"),("size_bool","R1_DATABASE_METADATA_SIZE_INVALID"),("base_hash","E10:"),("existing_output","R1_ARM_OUTPUT_EXISTS"),("outside_output","R1_ARM_OUTPUT_OUTSIDE_WORKSPACE")):
    v=copy.deepcopy(selection);m=copy.deepcopy(metadata);bp=base;out=workspace/("negative_"+case)
    if case=="bad_digest":v["regenerated_sha256"]="bad"
    elif case=="no_rows":v["rows"]=0
    elif case=="row_type":v["rows"]=True
    elif case=="no_ids":v["row_id_digest"]=""
    elif case=="no_inputs":v["inputs_pinned"]=None
    elif case=="bad_path":v["logical_output"]="/tmp/elsewhere"
    elif case=="no_db":v["inputs_pinned"].pop("routing_database")
    elif case=="bad_base":v["inputs_pinned"]["routing_base"]["sha256"]="bad"
    elif case=="wrong_db":v["inputs_pinned"]["routing_database"]["sha256"]="0"*64;m["files"][0]["sha256"]="0"*64
    elif case=="metadata_type":m["files"]={}
    elif case=="metadata_missing":m["files"]=[]
    elif case=="size_bool":m["files"][0]["size"]=True
    elif case=="base_hash":bp=F/"db_bytes.json"
    elif case=="existing_output":out=workspace/"out/armed"
    elif case=="outside_output":out=L/"out/not_an_arm_output"
    p=N/(case+"_selection.json");q=N/(case+"_metadata.json");J.write(p,v);J.write(q,m)
    reviewed=v.get("regenerated_sha256")
    if not isinstance(reviewed,str) or len(reviewed)!=64:reviewed=selection["regenerated_sha256"]
    verdict=N/(case+"_RESULT.txt");verdict.write_text("Synthetic test only: PASS\n"+J.sha(p)+"\n"+reviewed+"\n")
    auth=dict(reviewed_selection_sha256=J.sha(p),reviewed_regenerated_sha256=reviewed,review_verdict=verdict)
    with patch.object(arm,"L",workspace):
        try:arm.apply(p,q,out,base_path=bp,**auth)
        except ValueError as e:assert str(e).startswith(code),(case,str(e));records.append(dict(case=case,refusal=str(e)))
        else:raise AssertionError("invalid input accepted: "+case)
sys.settrace(None)
J.write(D/"ARM_NEGATIVES.json",dict(status="PASS",records=records,covered={k:sorted(v) for k,v in hits.items()}))
print("Arming negative controls PASS",len(records),flush=True)

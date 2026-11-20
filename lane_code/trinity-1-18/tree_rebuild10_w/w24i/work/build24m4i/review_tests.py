from pathlib import Path
from common import *
import copy,importlib.util,subprocess,io,contextlib
from unittest.mock import patch
F=D/"arming_final";workspace=F/"workspace";N=D/"review_negatives";N.mkdir()
sp=importlib.util.spec_from_file_location("arm_review",L/"out/arm_routing.py");arm=importlib.util.module_from_spec(sp);sp.loader.exec_module(arm)
selection=J.load(F/"routing_selection.json");dh=selection["regenerated_sha256"];sh=J.sha(F/"routing_selection.json")
auth=dict(reviewed_selection_sha256=sh,reviewed_regenerated_sha256=dh,review_verdict=F/"REVIEW_RESULT.txt")
records=[]
def refuse(case,code,*,value=None,auth_changes=None,metadata=None,base=None,output=None,omit=None,fresh_review=False):
    s=F/"routing_selection.json";m=F/"db_bytes.json";a=dict(auth)
    if value is not None:s=N/(case+"_selection.json");J.write(s,value)
    if metadata is not None:m=N/(case+"_db.json");J.write(m,metadata)
    if fresh_review:
        v=N/(case+"_RESULT.txt");v.write_text("Synthetic test only: PASS\n"+J.sha(s)+"\n"+J.load(s)["regenerated_sha256"]+"\n")
        a.update(reviewed_selection_sha256=J.sha(s),reviewed_regenerated_sha256=J.load(s)["regenerated_sha256"],review_verdict=v)
    a.update(auth_changes or {})
    if omit:a.pop(omit)
    target=output or workspace/("negative_"+case)
    existed=target.exists()
    with patch.object(arm,"L",workspace):
        try:arm.apply(s,m,target,base_path=base or F/"base.json",**a)
        except (ValueError,TypeError,FileNotFoundError) as e:
            assert code in str(e),(case,str(e),code)
            records.append(dict(case=case,refusal=str(e),output_created=False))
        else:raise AssertionError("accepted "+case)
    assert target.exists()==existed
for field in auth:refuse("missing_"+field,field,omit=field)
for field in ("reviewed_selection_sha256","reviewed_regenerated_sha256"):
 for bad in ("e"*63,"g"*64,"e"*65,None):refuse("malformed_"+field+"_"+str(len(str(bad))),"R1_REVIEW_HASH_INVALID",auth_changes={field:bad})
refuse("mismatched_reviewed_selection","R1_REVIEWED_SELECTION_DIFFERS",auth_changes=dict(reviewed_selection_sha256="0"*64))
for field,value in (("rows",selection["rows"]+17),("row_id_digest","f"*64),("regenerated_sha256","e"*64)):
 v=copy.deepcopy(selection);v[field]=value
 refuse("tampered_"+field,"R1_REVIEWED_SELECTION_DIFFERS",value=v)
v=copy.deepcopy(selection);v["regenerated_sha256"]="e"*64
refuse("fabricated_regenerated_with_matching_test_verdict","R1_ROUTING_REGENERATED_DATABASE_DIFFERS",value=v,fresh_review=True)
# Replay the exact retained fabricated selection cited by the reviewer.
probe=J.load(L/"work/build24m4f/review_negatives/reviewer_fabricated_selection_probe_selection.json")
assert probe["regenerated_sha256"]=="e"*64
refuse("reviewer_fabricated_selection_probe","R1_ROUTING_REGENERATED_DATABASE_DIFFERS",value=probe,metadata=J.load(L/"work/build24m4f/review_negatives/reviewer_fabricated_selection_probe_db.json"),fresh_review=True)
for case,text,code in (("fail","FAIL\n"+sh+"\n"+dh,"R1_REVIEW_VERDICT_NOT_PASS"),("substring_pass","BYPASS\n"+sh+"\n"+dh,"R1_REVIEW_VERDICT_NOT_PASS"),("no_selection","PASS\n"+dh,"R1_REVIEW_VERDICT_HASH_MISSING"),("no_regenerated","PASS\n"+sh,"R1_REVIEW_VERDICT_HASH_MISSING"),("embedded_hash","PASS\n0"+sh+"0\n"+dh,"R1_REVIEW_VERDICT_HASH_MISSING")):
 p=N/(case+"_RESULT.txt");p.write_text(text);refuse(case,code,auth_changes=dict(review_verdict=p))
p=N/"wrong_regenerated_RESULT.txt";p.write_text("PASS\n"+sh+"\n"+"0"*64)
refuse("mismatched_reviewed_regenerated","R1_REVIEWED_REGENERATED_DIFFERS",auth_changes=dict(reviewed_regenerated_sha256="0"*64,review_verdict=p))
refuse("missing_verdict_file", "No such file",auth_changes=dict(review_verdict=N/"absent_RESULT.txt"))
# Reauthenticate deliberately invalid fixture bytes to exercise retained checks.
for field,value,code in (("rows",0,"R1_ROUTING_SELECTION_PIN_INVALID"),("rows",True,"R1_ROUTING_SELECTION_PIN_INVALID"),("row_id_digest","","R1_ROUTING_SELECTION_PIN_INVALID"),("inputs_pinned",None,"R1_ROUTING_SELECTION_PIN_INVALID"),("logical_output","/tmp/other","R1_ROUTING_SELECTION_PATH_DIFFERS")):
 v=copy.deepcopy(selection);v[field]=value
 refuse("invalid_"+field+"_"+str(value),code,value=v,fresh_review=True)
refuse("base_hash","E10:",base=F/"db_bytes.json")
refuse("existing_output","R1_ARM_OUTPUT_EXISTS",output=workspace/"out/armed")
refuse("outside_output","R1_ARM_OUTPUT_OUTSIDE_WORKSPACE",output=L/"out/not_an_arm_output")
refuse("metadata_type","R1_DATABASE_METADATA_INVALID",metadata=dict(files={}))
refuse("metadata_bool_size","R1_DATABASE_METADATA_SIZE_INVALID",metadata=dict(files=[dict(sha256=dh,size=True)]))
# Exercise real CLI parsing and success output without creating a second set of kits.
cli=[str(L/"out/arm_routing.py"),str(F/"routing_selection.json"),str(F/"db_bytes.json"),"--output",str(workspace/"cli_never_created")]
flags=[("--reviewed-selection-sha256",sh),("--reviewed-regenerated-sha256",dh),("--review-verdict",str(F/"REVIEW_RESULT.txt"))]
for missing,_ in flags:
 args=[x for flag,value in flags if flag!=missing for x in (flag,value)]
 r=subprocess.run([sys.executable,"-I","-s","-B",*cli,*args],capture_output=True,text=True)
 assert r.returncode==2 and missing in r.stderr and not (workspace/"cli_never_created").exists()
 records.append(dict(case="cli_missing_"+missing,status="REFUSED",exit_code=r.returncode))
result=J.load(workspace/"out/armed/UPLOADS_ROUTING_ARMED.json")
with patch.object(sys,"argv",cli+[x for flag,value in flags for x in (flag,value)]),patch.object(arm,"apply",return_value=result) as apply:
 output=io.StringIO()
 with contextlib.redirect_stdout(output):arm.main()
 printed=json.loads(output.getvalue());assert printed["kits"]==result["kits"] and printed["armed_n_go_config"]==result["armed_n_go_config"]
 assert all(apply.call_args.kwargs[k]==v for k,v in auth.items())
J.write(D/"REVIEW_AUTH_TESTS.json",dict(status="PASS",records=records,cli_success_output=printed,cli_success_scope="main parser and output with captured successful apply result; real apply and native q planner run in ARM_TESTS.json",all_negative_outputs_absent=True,synthetic_review_only=True))
print("Review authentication tests PASS",len(records),flush=True)

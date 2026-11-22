R=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa
python3 - <<'P'
import json
R="/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/"
def show(o,p="",dep=0):
    if isinstance(o,dict):
        for k,v in o.items():
            if k=="h1": print(p+"/h1 <skipped>");continue
            if isinstance(v,(dict,list)) and dep<3: show(v,p+"/"+k,dep+1)
            else: print(p+"/"+k,"=",str(v)[:80])
    elif isinstance(o,list):
        print(p,"list len",len(o))
        if o: show(o[0],p+"[0]",dep+1)
with open(R+"metrics_172660.jsonl") as f:
    d=json.loads(f.readline())
print("TOP",[k for k in d]); show(d["ranks"][0],"rank0")
print("nranks",len(d["ranks"]))
P
echo ---d; ls -la $R/d | head; ls $R/d/* | head -20
echo ---m400; ls -la $R/m400 | head -20
echo ---m600; ls -la $R/m600 | head -20
echo ---inputs; ls $R/inputs | head
echo ---runjson; head -c 600 $R/run_172660.json
echo; ls -la /project/community/jjyeung/okh7/x_ee227714/o | head -20

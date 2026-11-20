from pathlib import Path
import json,runpy
L=Path.cwd();D=L/"work/build24m4y"
p=D/"EXTRA_RUNS.json";r=json.loads(p.read_text());r.append(json.loads((D/"CONTRACT_FINAL_RUN.json").read_text()))
a=L/"attic/build24m4y/EXTRA_RUNS_before_final.json";a.parent.mkdir(parents=True,exist_ok=True);p.rename(a);p.write_text(json.dumps(r,indent=2)+"\n")
runpy.run_path(str(D/"input_audit.py"),run_name="__main__")
runpy.run_path(str(D/"validate_w.py"),run_name="__main__")

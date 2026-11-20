from pathlib import Path
from common import *
import runpy,ast,importlib.util,io,contextlib
from unittest.mock import patch
hits=set();target=str(L/"out/arm_routing.py")
def trace(frame,event,arg):
 if frame.f_code.co_filename==target:
  if event=="line":hits.add(frame.f_lineno)
  return trace
 return None
# Reuse negative inputs; every rejected output remains absent.
s=(D/"review_tests.py").read_text().replace('N.mkdir()','N.mkdir(exist_ok=True)')
sys.settrace(trace)
exec(compile(s,str(D/"review_tests.py"),"exec"),{"__name__":"__main__","__file__":str(D/"review_tests.py")})
sp=importlib.util.spec_from_file_location("arm_cli",target);arm=importlib.util.module_from_spec(sp);sp.loader.exec_module(arm)
F=D/"arming_final";workspace=F/"workspace"
args=[target,str(F/"routing_selection.json"),str(F/"db_bytes.json"),"--reviewed-selection-sha256",J.sha(F/"routing_selection.json"),"--reviewed-regenerated-sha256",J.load(F/"routing_selection.json")["regenerated_sha256"],"--review-verdict",str(F/"REVIEW_RESULT.txt"),"--routing-base",str(F/"base.json"),"--output",str(workspace/"out/cli_armed")]
with patch.object(arm,"L",workspace),patch.object(sys,"argv",args):
 output=io.StringIO()
 with contextlib.redirect_stdout(output):arm.main()
 printed=json.loads(output.getvalue())
sys.settrace(None)
record=J.load(workspace/"out/cli_armed/UPLOADS_ROUTING_ARMED.json")
assert printed["kits"]==record["kits"]
assert printed["armed_n_go_config"]==record["armed_n_go_config"]
for name,seal in printed["kits"].items():assert J.seal(workspace/"out/cli_armed/kits"/name)==seal
source=Path(target).read_text();statements={n.lineno for n in ast.walk(ast.parse(source)) if isinstance(n,ast.stmt)}
J.write(D/"ARM_COVERAGE.json",dict(status="PASS",source_sha256=J.sha(target),executed_lines=sorted(hits),statement_lines=sorted(statements),uncovered_statement_lines=sorted(statements-hits),cli_output=printed,scope="Real main(), apply(), scans and closure; negative review and retained checks. External native planner runs recorded in ARM_TESTS.json."))
print("Real CLI armed seals and config hashes PASS",flush=True)

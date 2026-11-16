"""Diagnostic line trace; never claim production branch or whole-worker coverage."""
import dis,json,runpy,sys,trace,types
from pathlib import Path
B=Path(__file__).resolve().parents[1]
R=B/'out/c8/sources/sj/orch_cd/evalx/work/milestone'
tracer=trace.Trace(count=True,trace=False)
argv=sys.argv
sys.argv=[str(B/'out/tests/test_core.py')]
try:
    try:tracer.runfunc(runpy.run_path,str(B/'out/tests/test_core.py'),run_name='__main__')
    except SystemExit as e:
        if e.code:raise
finally:sys.argv=argv
counts=tracer.results().counts
def executable(code):
    values={n for _,n in dis.findlinestarts(code) if n>0}
    for sub in code.co_consts:
        if isinstance(sub,types.CodeType):values.update(executable(sub))
    return values
files={}
for p in sorted(R.rglob('*.py')):
    code=compile(p.read_text(),str(p),'exec')
    lines=executable(code)
    executed={line for (name,line),count in counts.items() if name==str(p) and count}
    files[str(p.relative_to(R))]=dict(executable_lines=sorted(lines),executed_lines=sorted(executed),
                                  missed_lines=sorted(lines-executed))
out=B/'out/coverage'
(out/'CORE_DIAGNOSTIC.json').write_text(json.dumps(dict(
    interpreter=sys.version,branch_coverage=False,whole_worker=False,files=files),indent=2)+'\n')
table='# Unexecuted C8 source lines\n\n'
table+='Neither whole-worker mode executed. This conservative inventory includes all executable lines, including CLI paths outside either mode. It is not a reachability proof. System-Python core-test line evidence is separated from production branch coverage.\n\n'
table+='| File | Not executed by either rehearsal or core tests | Reason |\n|---|---|---|\n'
unexecuted=0
for name,value in files.items():
    missing=value['missed_lines'];unexecuted+=len(missing)
    table+='| `'+name+'` | '+', '.join(map(str,missing))+' | Runtime/input blocked; numerical tests and both worker modes unexecuted. |\n'
table+='\nThe native_worker.full body, full report tail, and IN_JOB_ADMISSION are unexecuted findings. No full-read admission exists.\n'
(out/'UNEXECUTED.md').write_text(table)
for mode in ('pilot','full'):
    directory=out/mode;directory.mkdir(exist_ok=True)
    (directory/'coverage.json').write_text(json.dumps(dict(status='NOT_EXECUTED',branch_coverage=False,
        mode=mode,reason='Required Python and streamed assets absent',files={n:dict(
            executed_lines=[],missing_lines=v['executable_lines']) for n,v in files.items()}),indent=2)+'\n')
(out/'SUMMARY.json').write_text(json.dumps(dict(
    core_diagnostic_executed_lines=sum(len(v['executed_lines']) for v in files.values()),
    conservative_unexecuted_lines=unexecuted,source_files=len(files),
    pilot=dict(status='BLOCKED',executed_lines=0,branch_coverage=None),
    full=dict(status='BLOCKED',executed_lines=0,branch_coverage=None)),indent=2)+'\n')

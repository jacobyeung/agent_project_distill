import sys,json,runpy,os
script,out=sys.argv[1],sys.argv[2]
T='/scratch/jjyeung/orch_n30/review_tree11/pkg/work/tree_r1/'
want={T+'student_pilot/carrier_c1_run.py':{71,72,672,674,1388,2304},T+'student_pilot/verify_pass.py':{330}}
hit={k:set() for k in want}
M=sys.monitoring;M.use_tool_id(4,'rev11')
def line(code,ln):
    f=code.co_filename
    if f in want:
        if ln in want[f]: hit[f].add(ln)
        return None
    return M.DISABLE
M.register_callback(4,M.events.LINE,line);M.set_events(4,M.events.LINE)
sys.argv=[script]
rc='ok'
try: runpy.run_path(script,run_name='__main__')
except SystemExit as e: rc=f'exit {e.code}'
except Exception as e: rc=f'{type(e).__name__}: {e}'[:300]
M.set_events(4,0)
r=dict(script=script,rc=rc,hit={os.path.basename(k):sorted(v) for k,v in hit.items()})
json.dump(r,open(out,'w'));print(json.dumps(r))

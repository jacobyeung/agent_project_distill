from pathlib import Path
import runpy
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
s=(L/'work/build23/lookahead_after.py').read_text().replace("D=L/'work/build23'", "D=L/'work/build23b'")
s=s.replace("ns+'/minimal'", "ns+'/minimal23b'").replace("node/'minimal/q/RESULT.json'", "node/'minimal23b/q/RESULT.json'")
s=s.replace("print(json.dumps(dict(runs=records,result=result),indent=2))", "print(json.dumps(dict(runs=[dict(stage=r['stage'],returncode=r['returncode']) for r in records],refusal=result.get('refusal') if result else None)))")
(D/'lookahead_run.py').write_text(s);runpy.run_path(str(D/'lookahead_run.py'),run_name='__main__')

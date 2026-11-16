import os,sys,json,copy,tempfile
from pathlib import Path
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
sys.path.insert(0,str(Path(__file__).parent))
import gate,prooflib,render
import bindings as B,pipeline as P,rehearse
from boundaries import CPU
STATE={}
def p4():
 import torch
 torch.set_num_threads(1)
 root=Path(tempfile.mkdtemp(prefix='p4_',dir=prooflib.LANE/'work'))
 c,ex=rehearse.fixture(root/'input');P.run_capture(c,ex,CPU(),root/'cache')
 results=B.load(root/'cache/responses.json');rows=render.from_capture(c,root/'cache',fixture=True)
 assert [r['label'] for r in rows]==['trust','fallback','excluded'],[r['label'] for r in rows]
 source=c['rows'][0];original=results[0];mutant=copy.deepcopy(original)
 mutant['calls'][-1]['response']=f"distance {source['gt_value']:.2f} m"
 try:render.render(source,mutant,c,expected_calls_sha256=B.digest(original['calls']),backend_hashes={'fixture':'a'*64},fixture=True)
 except ValueError:pass
 else:raise AssertionError('Injected GT response passed')
 bad=copy.deepcopy(c['rows'][1]);bad['fallback']['trace']='I cannot answer from these frames.'
 try:render.render(bad,results[1],c,expected_calls_sha256=B.digest(results[1]['calls']),backend_hashes={'fixture':'a'*64},fixture=True)
 except ValueError:pass
 else:raise AssertionError('Refusal fallback passed')
 for r in rows[:2]:
  assert r['response_loss_weight']==0 and len(r['frame_sha256'])==32
  assert all(r['target'][s['start']:s['end']].startswith('<tool_response>') for s in r['tool_output_spans'])
 counts=render.write_rows(rows,root/'rendered');STATE.update(root=root,c=c,rows=rows)
 return dict(fixture=str(root),counts=counts,gt_injection_refused=True,fallback_refusal_refused=True,runtime_status_bytes_exact=True,reused=['o3_cache/work/kit/rehearse.py','o3_cache/work/kit/pipeline.py','o3_cache/work/kit/boundaries.py'],scope='Real dense geometry conversion, proposals, native selector, runtime calls and renderer; neural outputs only are synthetic')
def p7():
 import student_pilot
 tree=gate.ROOT/'rs_tree/work/tree_r1'
 student_pilot.__path__.insert(0,str(tree/'student_pilot'))
 from student_pilot import r1_contract as C
 from student_pilot.p3_provenance import file_pin
 root=STATE['root'];fixture=[]
 inv=B.load(prooflib.LANE/'out/CAPTURES.json');canon=inv['pilot'][0]['canonical']
 for i in range(32):
  r=copy.deepcopy(STATE['rows'][i%2]);r['qid']='b6-cpu-fixture-'+str(i);r['canonical']=canon;r['provenance']['canonical']=canon
  r['provenance']['fixture_warning']='Synthetic neural boundary, never a training admission';fixture.append(r)
 membership=root/'membership.json';membership.write_text(json.dumps(dict(schema='r1-trace-membership-v1',rows={r['qid']:C.row_binding(r) for r in fixture})))
 spec=B.load(gate.ROOT/'rs_tree/work/tests/contract.json');spec['membership']=file_pin(membership)
 admission=C.Admission(spec)
 for r in fixture:admission.check(r)
 out=prooflib.LANE/'out/FIRST_BATCH_32.jsonl';out.write_text(''.join(json.dumps(r)+'\n' for r in fixture))
 (prooflib.LANE/'out/FIRST_BATCH_CONTRACT.json').write_text(json.dumps(spec,indent=2)+'\n')
 return dict(rows=32,trust=16,fallback=16,fixture_only=True,real_admission='student_pilot.r1_contract.Admission.check(require_frames=True)',rows_path=str(out),contract_path=str(prooflib.LANE/'out/FIRST_BATCH_CONTRACT.json'),production_call='for row in first_batch_rows: admission.check(row, require_frames=True)',tree_source_sha256=gate.sha(tree/'student_pilot/r1_contract.py'))
if __name__=='__main__':
 ok=prooflib.run('P4',p4)
 if ok:ok=prooflib.run('P7',p7)
 raise SystemExit(not ok)

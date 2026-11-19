from pathlib import Path
import ast,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24h'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
cfg=J.load(L/'out/N_PRODUCTION_CONFIG.json');own=J.load(D/'sequence_final/n/own.json');result_path=D/'sequence_final/n/q_22c714e1_20/p/q/RESULT.json';result=J.load(result_path) if result_path.exists() else {'refusal':J.load(D/'SEQUENCE.json')['n']['first_refusal']}
def differences(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  return [r for k in sorted(set(a)|set(b)) for r in differences(a.get(k),b.get(k),path+'/'+k)]
 if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
  return [r for i,(x,y) in enumerate(zip(a,b)) for r in differences(x,y,path+'/'+str(i))]
 return [] if a==b else [dict(field=path,canary_input=a,localised_input=b)]
source=(L/'work/tree_r1/launch_r1/production_proof.py').read_text();tree=ast.parse(source)
calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
assert not any('frame_host' in n for n in calls)
assert 'config' not in result
host=J.load(L/'work/build24/kits/n/k/h.json')
J.write(D/'IDENTITY_COMPARISON.json',dict(status='BLOCKED_FINAL_IDENTITY',localised_input_identity=(L/'out/N_IDENTITY.txt').read_text().strip(),hidden_view_roots=['/scratch/jjyeung','/home','/data','/data2','/data3'],canary_result=str(D/'sequence_final/n/q_22c714e1_20/p/q/RESULT.json'),canary_result_present=result_path.exists(),canary_final_config_present=False,canary_refusal=result['refusal'],localisation_differences=differences(own,cfg),production_q_calls_frame_host=False,host_request_missing=[k for k in ('staging','routing_selection','routing_base') if not host.get(k)],safe_to_equate_input_and_final_identity=False))
print('production host producer and final identity BLOCKED; exact differences recorded')

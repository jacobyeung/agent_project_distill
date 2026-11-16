import sys,json,hashlib
kit=sys.argv[1]
sys.path[:0]=[kit+'/work',kit+'/native_kit']
import bindings as B
s=B.source_identity()
b=json.load(open('/scratch/jjyeung/k1/run_tower_sam_2/BINDING.json'))
L='/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a';C='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/kc'
mapped={k.replace('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/kc','/scratch/jjyeung/orch_n30/k1_ops3/kc'):v for k,v in s.items()}
print('n',len(s),'binding keys',sorted(b))
print('sources equal BINDING (mapped):',mapped==b['sources'])
print('BINDING manifest',b.get('manifest_sha256','')[:8],'producer',b.get('producer_sha256','')[:8],'phase',b.get('phase'))
print('k1_phases sha',hashlib.sha256(open(kit+'/work/k1_phases.py','rb').read()).hexdigest()[:8])
print('changed files in identity:',[k for k in s if any(k.endswith(n) for n in ['k1_pipeline.py','k1_cli.py','k1_report.py','train.py','gt_set.py'])])

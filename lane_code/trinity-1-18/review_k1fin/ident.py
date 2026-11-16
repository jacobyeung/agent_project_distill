import sys,json,hashlib,importlib.util
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('fk','/scratch/jjyeung/orch_n30/k1_ops3/work/codex_finalize_v2/finalize_k1.py'); fk=importlib.util.module_from_spec(spec); spec.loader.exec_module(fk)
m=fk.finalize(fk.load_bundle())
raw=(json.dumps(m,indent=2,allow_nan=False)+'\n').encode()
print('rerun sha',hashlib.sha256(raw).hexdigest())
W='/scratch/jjyeung/orch_n30/k1_ops3/work/'
S=json.load(open(W+'K1_MANIFEST.staged.json')); base=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/out/K1_MANIFEST.base.json')); par=json.load(open(W+'PARITY_FINAL.json'))
pins={(c['canonical'],f['index']):f['sha256'] for c in base['captures'] for f in c['dense_frames'] if f.get('sha256')}
new={(cn,x['index']):x['sha256'] for cn,xs in par['new'].items() for x in xs}
ok=bad=0;anch=0
for c in S['captures']:
    for f in c['dense_frames']:
        k=(c['canonical'],f['index']); w=pins.get(k) or new.get(k)
        if w and f['sha256']==w and f['path']=='/scratch/jjyeung/k1_frames/%s/%s.png'%(w[:2],w): ok+=1
        else: bad+=1
    si=c['model_row']['student_input']
    anch+= [x['sha256'] for x in si['frames']]==[c['dense_frames'][i]['sha256'] for i in c['anchor_slots']] and si['frame_indices']==c['anchor_indices']
print('base pins',len(pins),'new',len(new),'overlap',len(set(pins)&set(new)),'frames ok',ok,'bad',bad,'anchors ok',anch)

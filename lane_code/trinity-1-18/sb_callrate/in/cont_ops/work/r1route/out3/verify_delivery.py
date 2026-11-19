from pathlib import Path
import ast,collections,hashlib,io,json,os,re,subprocess,tarfile
R=Path(__file__).resolve().parent;W=R.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
proof={'packages':{},'operator_syntax':[],'python36_compile':[],'operator_guards':[]}
settings=json.loads((R/'pins/R1_READ_SETTINGS_PLAN_ENTRY.json').read_text())
for k,label in [('b1','A'),('b2','B')]:
 o=R/label;base=R/'bases'/k
 def members(path):
  with tarfile.open(path) as t:
   ms=t.getmembers();assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in ms)
   assert len(ms)==len(set(m.name for m in ms))
   return {m.name:t.extractfile(m).read() for m in ms}
 delivery=members(o/'1.tgz');payload=members(o/'0.tgz');old=members(base/'0.tgz');cfg=json.loads(payload['9.json']);public=json.loads(delivery['0.json']);plan=json.loads((o/'READ_PLAN.json').read_text())
 assert delivery['0.tgz']==(o/'0.tgz').read_bytes()
 assert delivery['PACKAGE.json']==(o/'PACKAGE.json').read_bytes()
 assert sha(payload['9.json'])==sha((o/'src/9.json').read_bytes())
 assert public['plan_sha256']==sha(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode())
 assert sha(delivery['0.tgz'])==public['payload_sha256']
 for n,h in json.loads(delivery['PACKAGE.json'])['files'].items():assert sha(delivery[n])==h
 for n,pin in cfg['payload_pins'].items():assert pin==dict(bytes=len(payload[n]),sha256=sha(payload[n]))
 for n in payload:
  if n.startswith(('b/','tree/','h1eval/','items/','rows/','auth/')):assert old[n]==payload[n]
 assert plan['token']==public['token']==cfg['token']==(o/'TOKEN').read_text().strip()
 assert re.fullmatch('[a-f][0-9a-f]{12}',cfg['token'])
 assert json.loads(delivery['a/1.json'])==json.loads(delivery['a/export.json'])=={'pending':True}
 assert delivery['a/4.py']==(o/'fill_export.py').read_bytes()
 assert delivery['a/5.py']==(o/'node_check.py').read_bytes()
 assert delivery['a/6.py']==(o/'tower_sequence.py').read_bytes()
 for key,value in settings.items():assert plan['read_settings'][0][key]==value,(label,key)
 for key in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth'):assert cfg[key]==settings[key]
 manifest=json.loads(payload['items/devs1_routed.json' if label=='A' else 'items/room134.json']);types=[cfg['order'][i] for i in plan['read_settings'][0]['types']]
 ids=[it['id'] for t in types for it in sorted(manifest['items'],key=lambda x:x['id']) if it['question_type']==t]
 assert ids==plan['item_ids_in_execution_order'],label
 assert len(ids)==(636 if label=='A' else 134)
 baseplan=json.loads((base/'READ_PLAN.json').read_text());basecfg=json.loads(old['9.json']);basetypes=[basecfg['order'][i] for i in baseplan['read_settings'][0]['types']]
 baseids=[it['id'] for t in basetypes for it in sorted(manifest['items'],key=lambda x:x['id']) if it['question_type']==t]
 assert ids==baseids
 if label=='A':assert sum(it['question_type'].startswith('camera_') for it in manifest['items'])==450
 else:assert {n:len(v) for n,v in manifest['sets'].items()}=={'dev-S1':36,'R0-dev':98}
 timing=json.loads((o/'TIME_PRICE.json').read_text());estimate=(sum(s['seconds'] for s in timing['segments'])+timing['measured_nondecode_seconds']) if label=='A' else timing['measured_read_seconds']+timing['staging_allowance_seconds']
 assert abs(estimate-timing['estimated_completion_seconds'])<1e-8
 assert cfg['budget_gpu_seconds']==timing['allocated_seconds']
 assert timing['stop_at_seconds']==timing['allocated_seconds']-1800
 binding=cfg['export_binding'];assert binding==json.loads((W/'out/EXPORT_BINDING.json').read_text())
 assert {n:binding[n] for n in ('run','step','member_directory','lineage','object')}==dict(run='673bc60f',step=200,member_directory='m200',lineage='SFT',object='q8/8865619b/673bc60f_m200.tar')
 for n,p in [('config',W/'in/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json'),('receipt',W/'in/s1/s1_receipt.json'),('data_receipt',W/'in/data_receipt.json')]:assert sha(p.read_bytes())==binding['preparation_sha256'][n]
 c=json.loads((W/'in/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json').read_text());receipt=json.loads((W/'in/s1/s1_receipt.json').read_text())
 assert c['preparation']['sha256']==binding['preparation_sha256']['receipt'];assert receipt['config_sha256']==binding['config_sha256'];assert c['base_identity']==binding['base_identity'];assert receipt['frame_layout']==c['frame_layout']==binding['frame_layout']=='duplicate'
 for name in ('o_place.sh','o_pullfill.sh','o_cpucheck.sh','o_sub.sh','o_fetch.sh'):
  subprocess.run(['bash','-n',str(o/name)],check=True);proof['operator_syntax'].append(label+'/'+name)
 helper_names=['src/8.py','src/orchard_h10/common.py','src/orchard_h10/export_pins.py','src/orchard_h10/job.py','src/orchard_h10/vendor/export_stage.py','src/orchard_h10/vendor/orchard_job.py','src/orchard_h10/vendor/orchard_launcher.py','src/orchard_h10/vendor/orchard_results.py','fill_export.py','node_check.py','tower_bootstrap.py','tower_sequence.py','package/3.py','fetch_return.py','unpack_return.py']
 code='import sys\nfrom pathlib import Path\nfor p in sys.argv[1:]:compile(Path(p).read_bytes(),p,"exec")\nprint(sys.version.split()[0])'
 result=subprocess.run(['/usr/bin/python3','-I','-s','-B','-c',code]+[str(o/n) for n in helper_names],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert result.returncode==0,result.stderr;proof['python36_compile']+= [label+'/'+n for n in helper_names]
 proof['packages'][label]=dict(token=cfg['token'],payload_members=len(payload),delivery_members=len(delivery),changed_payload_members=[n for n in payload if payload[n]!=old[n]],read_count=len(ids),item_counts=dict(collections.Counter(it['question_type'] for it in manifest['items'])),estimated_seconds=estimate,python=result.stdout.decode().strip(),sealed_binding=binding)
 # Exercise the delivery-directory condition independently, without placing anything.
 line=next(s for s in (o/'o_place.sh').read_text().splitlines() if s.startswith('[[ "$D"'))
 for val,ok in [('/project/community/jjyeung/okh7/a15_cot_ap0123af',True),('/project/community/jjyeung/okh7/a15_cot_apbad/name',False),('/project/community/jjyeung/okh7/a15_cot_apXYZ',False),('/tmp/a15_cot_ap0123af',False)]:
  rc=subprocess.run(['bash','-c',line],env=dict(os.environ,D=val)).returncode;assert (rc==0)==ok;proof['operator_guards'].append(dict(package=label,delivery=val,accepted=ok))
assert 'gsutil' not in (R/'B/o_pullfill.sh').read_text()
pull=(R/'A/o_pullfill.sh').read_text();assert pull.count('gsutil -o Boto:num_retries=0')==1 and 'for i in 0 1 2 3; do' in pull
node=ast.parse(next(s for s in pull.splitlines() if s.startswith('assert int(f[1])')))
for n,h,ok in [(21583032320,'795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b',True),(21583032320,'795ef9ef'+'0'*56,False),(1,'795ef9ef'+'0'*56,False),(21583032320,'0'*64,False)]:
 try:exec(compile(node,'done guard','exec'),{'f':['q8/8865619b/673bc60f_m200.tar',str(n),h]});passed=True
 except AssertionError:passed=False
 assert passed==ok;proof['operator_guards'].append(dict(tar_bytes=n,sha256=h,accepted=ok))
# Scoring mathematics are byte-for-byte AST-identical to the surviving implementation.
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
a=funcs(W/'out/score_r1route.py');b=funcs(R/'score_r1route.py');pure=['bootstrap','metrics','compare','unit_count'];assert all(a[n]==b[n] for n in pure);proof['unchanged_scoring_functions']=pure
proof['completed_tar_verification']=dict(status='receipt_verified_tar_not_local',receipt=(W/'in/gcs_673bc60f_m200.done.txt').read_text(),reason='Exact receipt and preparation files verified locally; 20 GiB artifact scan runs on Orchard.')
(R/'FINAL_VERIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:len(proof[k]) for k in ('operator_syntax','python36_compile','operator_guards')}));print('delivery checks passed')

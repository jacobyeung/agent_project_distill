import sys,copy,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin
from student_pilot.carrier_c1_run import identity
from launch_r1.build import verify
base=J.load(D/'ORIGINAL_KITS.json');delta=J.load(D/'CONFIG_DELTA.json');seals=J.load(D/'SEALS.json')
def recursive_diff(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  result=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:result.append(dict(path=path+'/'+k,before=a.get(k),after=b.get(k)))
   else:result+=recursive_diff(a[k],b[k],path+'/'+k)
  return result
 if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):return sum((recursive_diff(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [dict(path=path,before=a,after=b)]
carddiff=recursive_diff(delta['card_before'],delta['card_after'])
assert {x['path'] for x in carddiff}=={'/cells/0/rows_per_step','/cells/16/rows_per_step','/room_rows_per_step'}
files=inventory(T);tree=digest(files);assert tree=='0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de'
final={};changes={};diffs={}
for n in NAMES:
 k=kit(n);assert verify(k)==seals[n]
 assert J.load(k/'k/a.json')['GO']==J.load(k/'BUILD.json')['GO']==(n=='n_go')
 check_archive(file_pin(k/J.load(k/'k/a.json')['source']['path']),files)
 final[n]={str(p.relative_to(k)):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob('*') if p.is_file()}
 assert set(final[n])==set(base[n]);changes[n]=[rel for rel,v in final[n].items() if v!=base[n][rel]]
 assert set(changes[n])=={'k/c.json','k/n.json','k/8.json','k/p.json','k/s.json','BUILD.json','SHA256SUMS.txt'},changes[n]
 assert all(final[n][rel]==v for rel,v in base[n].items() if rel.startswith('b/'))
 diffs[n]={}
 for rel in changes[n]:
  archived=L/'attic/build24m4i'/k.relative_to(L)/rel
  assert J.sha(archived)==base[n][rel]['sha256']
  if rel in ('k/c.json','k/n.json'):
   before=J.load(archived);after=J.load(k/rel);rows=recursive_diff(before,after);diffs[n][rel]=rows
   for row in rows:
    assert any(h in str(row['before']) and new in str(row['after']) for h,new in delta['hash_replacements'].items()),row
   assert len(rows)==8
   assert identity(after)==J.load(D/'CONFIG_IDENTITIES.json')[n][rel]['after']
  if rel.startswith('k/') and rel not in ('k/c.json','k/n.json'):diffs[n][rel]=recursive_diff(J.load(archived),J.load(k/rel))
 for p in (k/'b').glob('*.py'):compile(p.read_text(),str(p),'exec')
 assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==seals[n]
# Verify card/population/indices coherence without claiming that placeholders are production data.
for key,pin in delta['after'].items():assert J.sha(input_file(pin['sha256']))==pin['sha256']
pop=J.load(input_file(delta['after']['population']['sha256']));idx=J.load(input_file(delta['after']['indices']['sha256']))
assert pop['complete'] is False and pop['after_all_filters'] is False and all(v==0 for v in pop['counts'].values())
assert pop['card_sha256']==delta['after']['card']['sha256'] and idx['population_sha256']==delta['after']['population']['sha256']
# The retry changes only the missing fixture; retain the original suite outcome separately.
tests=J.load(D/'TEST_RUNS.json');assert len(tests)==16
assert [r['name'] for r in tests if r['returncode']] == ['resolver600_tests']
log=(D/'resolver600_tests.log').read_text();assert '\nOK\n' in log and 'FAILED' not in log
for r in tests:
 if r['name']=='resolver600_tests':r.update(returncode=0,retry_reason='Missing local UPLOADS_n.json fixture restored',first_output='attic/build24m4i/resolver600_first/resolver600_tests.log')
replace(D/'TEST_RUNS.json',json.dumps(tests,indent=2)+'\n')
assert J.load(D/'NATIVE_ARM_TESTS.json')['source_seals']==seals
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=tree,kits=seals,config_identities=J.load(D/'CONFIG_IDENTITIES.json'),changed=changes,card_diff=carddiff,decoded_config_diffs=diffs,all_b_unchanged=True,all_tree_archives_unchanged=True,all_original_files_preserved=True,GO='false except out/kit_n_go',incomplete_population_still_requires_native_preparation=True))
# Authenticate the complete input-kit state against the supplied Orchard delta manifest.
baseline=L/'out/UPLOADS_24M4H.json';assert J.sha(baseline)==J.sha(W/'w24h/out/UPLOADS_24M4H.json')
bh=J.load(baseline)
for row in bh['files']:
 name,rel=row['name'].split('/',1)
 if name in base:assert base[name][rel]['sha256']==row['sha256'] and base[name][rel]['bytes']==row['bytes']
for name,h in bh['kits'].items():assert h==J.load(D/'BASE_SEALS.json')[name]
upload=D/'upload';upload.mkdir();rows=[]
def record(p,name):return dict(name=name,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action='replace',transfer='local-upload')
for n in ('q','n','qd'):
 for rel in sorted(changes[n]):
  target=upload/n/rel;target.parent.mkdir(parents=True,exist_ok=True);os.link(kit(n)/rel,target);rows.append(record(target,n+'/'+rel))
for pin in delta['after'].values():
 h=pin['sha256'];p=upload/'u'/h;p.parent.mkdir(exist_ok=True);os.link(input_file(h),p);row=record(p,'u/'+h);row['action']='add';rows.append(row)
replayed=copy.deepcopy(base)
for row in rows:
 name,rel=row['name'].split('/',1)
 if name in replayed:replayed[name][rel]=dict(sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
assert all(replayed[n]==final[n] for n in ('q','n','qd'))
up=dict(schema='build24m4i-upload-diff-v1',baseline='Orchard 24m4h kits',baseline_manifest='w24h/out/UPLOADS_24M4H.json',baseline_manifest_sha256=J.sha(baseline),baseline_kit_seals=J.load(D/'BASE_SEALS.json'),files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),stream_root=str(upload),kits={n:seals[n] for n in ('q','n','qd')},GO=False,n_go_upload_authorized=False,uploaded=False,launch_authorized=False,config_only=True,outside_kit_files=['u/'+p['sha256'] for p in delta['after'].values()])
J.write(L/'out/UPLOADS_24M4I.json',up);(L/'out/UPLOADS_24M4I.list').write_text(''.join(r['name']+'\n' for r in rows))
go=[record(kit('n_go')/rel,'n/'+rel) for rel,v in final['n_go'].items() if v!=final['n'][rel]]
assert {r['name'] for r in go}=={'n/k/a.json','n/BUILD.json','n/SHA256SUMS.txt'}
J.write(L/'out/UPLOADS_24M4I_GO.json',dict(schema='build24m4i-go-diff-v1',base_kit_seal=seals['n'],kit_seal=seals['n_go'],files=go,total_files=len(go),total_bytes=sum(r['bytes'] for r in go),upload_authorized=False))
J.write(D/'UPLOAD_RECONSTRUCTION.json',dict(status='PASS',baseline_manifest_sha256=up['baseline_manifest_sha256'],all_three_kits_match=True,n_go_excluded=True,tree_and_b_delta_files=0))
# Correct source anchors without rerunning either sampler.
for p in (D/'N_DRY_COUNT.json',D/'dry_count_n.py',L/'out/CASE_24M4I.md',L/'out/DRAW_TABLE_24M4I.md',D/'write_draw_table.py'):
 s=p.read_text().replace('r1_mix.py:78','r1_mix.py:68').replace('r1_mix.py:105','r1_mix.py:90').replace('r1_mix.py:36','r1_mix.py:35')
 if s!=p.read_text():replace(p,s)
print('INVARIANTS PASS; delta',len(rows),'files',up['total_bytes'],'bytes; GO delta',len(go))

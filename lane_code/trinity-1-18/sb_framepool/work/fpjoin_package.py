"""Validate the joins, preserve the existing package, and add consumption evidence."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'out'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def pin(p):return {'sha256':sha(p)}
d=json.load(open(OUT/'FPJOIN.json'));report=OUT/'FPJOIN_REPORT.md'
assert len(report.read_text().splitlines())<=80
assert len(d['captures'])==146 and len({c['token'] for c in d['captures']})==146
assert len(d['source_id_join'])==1193 and len({r['qid'] for r in d['source_id_join']})==1193
verified=0
for p,v in d['inputs'].items():assert sha(p)==v['sha256'],p;verified+=1
for name,s in d['streams'].items():
 assert s['admitted_target']['count']==0
 for k,v in s.items():
  if isinstance(v,dict) and 'rows' in v and 'count' in v:
   assert v['count']==len(v['rows'])==len(v['ids'])
   assert sum(v['question_types'].values())==v['count']
   assert sum(c['streams'][name][k]['count'] for c in d['captures'])==v['count'],(name,k)
assert sum(d['streams']['step544:pose/'+n]['admitted_total'] for n in ['a2v3','a3v2'])==194987
assert sum(d['streams']['step544:pose/'+n]['target_dropped_final_scene_filter']['count'] for n in ['a2v3','a3v2'])==15120
assert sum(d['streams']['step544:pose/'+n]['final_benchmark_dropped'] for n in ['a2v3','a3v2'])==27040
assert d['streams']['step544:pose/a3v2']['pre_mix_all_benchmark_rows_excluded']==0
assert not d['VSTI']['overlap_with_126']
assert all(not x['overlap_ids'] and not x['unresolved_ids'] for x in d['VSTI']['kit_sets'])
assert d['camera_full_rows']['count']==35423 and d['camera_full_rows']['target']['count']==0
assert all(x['admitted_target_count_receipt_supported']==0 for x in d['R1'].values())
validation={'command':'/usr/bin/python3 work/fpjoin_package.py','inputs':{str(p):pin(p) for p in [OUT/'FPJOIN.json',report,ROOT/'work/fpjoin_package.py',ROOT/'work/fpjoin_report.py']},'status':'PASS','report_lines':len(report.read_text().splitlines()),'input_hashes_verified':verified,'capture_count':146,'source_id_count':1193,'per_capture_sums':'PASS','admitted_targets_all_zero':'PASS','pose_final_BENCH_drops':27040,'pose_final_target_drops':15120,'VSTI_overlap':0}
vp=OUT/'FPJOIN_VALIDATION.json';vp.write_text(json.dumps(validation,indent=1)+'\n')
old=json.load(open(OUT/'PACKAGE_CONTENTS.json'))['members'];items={n:Path(v['source']) for n,v in old.items()}
def add(p,n=None):
 p=Path(p).resolve();n=n or str(p.relative_to(ROOT));items[n]=p
for n in ['FPJOIN_REPORT.md','FPJOIN.json','FPJOIN_VALIDATION.json']:add(OUT/n)
for p in (ROOT/'work').glob('fpjoin*.py'):add(p)
for n in ['fpjoin_preimages.json','fpjoin.log','fpjoin_invert.log']:add(ROOT/'work'/n)
# Include all inputs actually used by FPJOIN, including complete recovered scene/camera projections.
for p in d['inputs']:
 p=Path(p).resolve()
 if ROOT in p.parents:add(p)
 else:add(p,'fpjoin_evidence/'+sha(p)[:16]+'_'+p.name)
contents={n:{'sha256':sha(p),'bytes':p.stat().st_size,'source':str(p)} for n,p in sorted(items.items())}
manifest=OUT/'PACKAGE_CONTENTS.json'
manifest.write_text(json.dumps({'command':'/usr/bin/python3 work/fpjoin_package.py','inputs':{v['source']:{'sha256':v['sha256']} for v in contents.values()},'members':contents,'note':'FPJOIN_REPORT.md supplies the consumption verdict. Manifest excludes itself and the archive SHA256 sidecar.'},indent=1)+'\n');add(manifest)
archive=OUT/'sb_framepool.tar'
with tarfile.open(str(archive),'w') as tar:
 for n,p in sorted(items.items()):tar.add(str(p),arcname=n,recursive=False)
with tarfile.open(str(archive),'r:') as tar:
 assert len(tar.getmembers())==len(items)
 for m in tar:
  if m.name=='out/PACKAGE_CONTENTS.json':continue
  h=hashlib.sha256();f=tar.extractfile(m)
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
  assert h.hexdigest()==contents[m.name]['sha256'],m.name
h=sha(archive);(OUT/'sb_framepool.tar.sha256').write_text(h+'  sb_framepool.tar\n')
(ROOT/'STATUS.md').write_text('COMPLETE sb_fpjoin: out/FPJOIN_REPORT.md ('+str(validation['report_lines'])+' lines) and out/FPJOIN.json report zero admitted target rows in the step-544 leg; R1 pointing/pose share verified pins, and routing/VQA zeros are receipt-supported with missing row-level inputs named. The independent source-id and scene joins cover 1,193 qids and 146 captures. Final pose BENCH filtering removes 15,120 target rows; official VSTI scenes overlap 0 of the 126 STI/ReSTI captures. All input and packaged-member hashes and count invariants pass. out/sb_framepool.tar includes both reports, JSON, scripts, and recovered evidence; SHA256 '+h+'.\n')
print(json.dumps({'validation':'PASS','archive_sha256':h,'bytes':archive.stat().st_size,'members':len(items),'report_lines':validation['report_lines']}))

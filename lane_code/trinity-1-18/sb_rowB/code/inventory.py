import collections, hashlib, json, re, sqlite3, tarfile
from pathlib import Path
ROOT=Path('/scratch/jjyeung/orch_n30/sb_rowB')
MIRROR=Path('/scratch/jjyeung/n30_mirror')
STORE=MIRROR/'rows_r1/out/a2_vqa_v7'
FAMILIES=['camera_obj_rel_dist_v1','camera_obj_rel_dist_v2','camera_obj_rel_dist_v3','obj_obj_relative_pos_nf']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def wording(r):
 q=r['student_input']['question']
 q=re.sub(r'frame \d+ of \d+', 'frame {k} of 32', q)
 if r['question_type'].startswith('camera_'):return re.sub(r'\([^)]*\)', '({objects})',q)
 return re.sub(r'is .*? \[Near/Far\] compared to .*\?', 'is {a} [Near/Far] compared to {b}?',q)
def classify(r):
 k=r['provenance']['camera_frame']; citations=re.findall(r'locate the (.+?), first seen in frame (\d+)',r['target'])
 assert len(citations)==len(r['provenance']['instances'])
 at=sum(int(f)==k for _,f in citations);other=len(citations)-at
 return dict(cites_k=bool(at),cites_other=bool(other),all_at_k=not other,none_at_k=not at,mixed=bool(at and other),object_citations_at_k=at,object_citations_other=other)
def main():
 pins={str(STORE/n):sha(STORE/n) for n in ['BUILD_MANIFEST.json','FAMILY_INDEX_RANGES.json','COUNTS_V7.json','vqa/rows.sqlite']}
 assert pins[str(STORE/'vqa/rows.sqlite')]=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
 c=sqlite3.connect('file:'+str(STORE/'vqa/rows.sqlite')+'?mode=ro',uri=True)
 idx=json.loads((STORE/'FAMILY_INDEX_RANGES.json').read_text())['families'];rows=[]
 census={};examples=[]
 for f in FAMILIES:
  rr=[json.loads(raw) for a,b in idx[f] for raw, in c.execute('select row from rows where i between ? and ? order by i',(a,b))];rows+=rr
  by=collections.defaultdict(collections.Counter)
  for r in rr:by[wording(r)].update(dict(rows=1,**classify(r)))
  census[f]=dict(by)
  for w in by:
   for cat in ['none_at_k','cites_k','cites_other','all_at_k']:
    subset=[r for r in rr if wording(r)==w and classify(r)[cat]][:20]
    examples.append('## '+f+' | '+w+' | '+cat+' ('+str(len(subset))+' available up to 20)\n')
    for r in subset:examples.append('### '+r['qid']+'\n'+r['student_input']['question']+'\n'+str(r['student_input']['options'])+'\n\n```text\n'+r['target']+'\n```\n')
 (ROOT/'inputs/sources.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
 result=dict(input_sha256=pins,families=census,total=len(rows),classification='cites_k and cites_other overlap on mixed rows; all_at_k and none_at_k are disjoint')
 (ROOT/'out/CENSUS.json').write_text(json.dumps(result,indent=2)+'\n')
 (ROOT/'out/EXAMPLES.md').write_text('\n'.join(examples))
 print(json.dumps(result,indent=2),flush=True)
 names={Path(r['provenance']['raster']).name for r in rows};hits=[];catalog=[]
 paths=sorted(p for p in MIRROR.rglob('*') if p.is_file() and p.suffix in ('.tar','.tgz') or p.is_file() and p.name.endswith('.tar.gz'))
 for p in paths:
  matches=[]
  with tarfile.open(p) as t:
   for m in t:
    if m.isfile() and Path(m.name).name in names:
     matches.append(dict(archive=str(p),member=m.name,size=m.size,offset=m.offset_data))
  catalog.append(dict(path=str(p),bytes=p.stat().st_size,matches=len(matches)));hits+=matches
  if matches:print(p.name,len(matches),flush=True)
 # Only candidate filenames are an index, never evidence of identity; build checks full source SHA.
 direct=[str(p) for p in MIRROR.rglob('*.npz') if p.name in names]
 (ROOT/'inputs/GT_LOCATIONS.json').write_text(json.dumps(dict(input_sha256=pins,archive_inventory=catalog,candidates=hits,direct=direct),indent=2)+'\n')
 print('GT candidate members',len(hits),'unique filenames',len({Path(x['member']).name for x in hits}),'needed',len(names),'direct',len(direct),flush=True)
 (ROOT/'STATUS.md').write_text('Stage 1 complete: CENSUS.json records all four distance families and EXAMPLES.md prints up to 20 full question/trace examples per citation class and wording. GT_LOCATIONS.json inventories exact-name candidates in local mirror archives; each candidate still requires a match to the source raster SHA. N’s direct grammar rejects numeric measurements, so reconstruction and admission remain separate checks.\n')
if __name__=='__main__':main()

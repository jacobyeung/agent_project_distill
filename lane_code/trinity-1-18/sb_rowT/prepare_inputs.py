"""Pin local inputs; stream v7 once; derive aliases only from recorded canonical/raster fields."""
import collections, csv, hashlib, json, re, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
B=W/'w19'; TREE=B/'work/tree_r1'
STORE=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
PIN='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 out=ROOT/'inputs';out.mkdir(exist_ok=True)
 pins={}
 def copy(p,name,expected=None):
  digest=sha(p)
  if expected:assert digest==expected,(p,digest,expected)
  dest=out/name;dest.write_bytes(p.read_bytes());pins[name]={'path':str(p),'sha256':digest};return dest
 assert sha(STORE)==PIN
 pins['store']={'path':str(STORE),'sha256':PIN}
 copy(W/'inputs/records/z.json','z.json')
 seal=copy(B/'out/TREE_SEAL.json','TREE_SEAL.json')
 comp=copy(B/'work/build19/inputs/component_rows.json','component_rows.json')
 authority=json.loads(comp.read_text())['proven']['authority']
 for k,v in authority.items():copy(Path(v['path']),k+'.json',v['sha256'])
 copy(B/'fixtures/work/shared/WITHHELD_ROOMS_80.json','withheld.json','634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed')
 copy(B/'fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json','dev.json','969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986')
 copy(B/'fixtures/work/records/revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json','bench.json','3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970')
 ids={json.loads(l)['row_key'] for l in (out/'z.json').open() if json.loads(l)['reason']=='count_diag_first_seen_list_form'}
 aliases=collections.defaultdict(dict);all_ids=[];cells=collections.Counter();found=set()
 def fact(r,canonical,field):
  if not isinstance(canonical,str) or '/' not in canonical:return
  ds,scene=canonical.split('/',1);native={'scannetpp':'scannetppv2'}.get(ds,ds)
  token='v'+hashlib.sha256(('rung1 scene '+native+'/'+scene).encode()).hexdigest()[:12]
  if r.get('scene')!=token:return
  canonical={'scannetppv2':'scannetpp'}.get(ds,ds)+'/'+scene
  aliases[r.get('dataset','')+'/'+token].setdefault(canonical,{'qid':r['qid'],'field':field})
 con=sqlite3.connect(STORE.as_uri()+'?mode=ro',uri=True)
 with (out/'removed_rows.jsonl').open('w') as f:
  for raw, in con.execute('SELECT row FROM rows ORDER BY i'):
   r=json.loads(raw);all_ids.append([r['qid'],r.get('candidate_id')])
   for field,obj in [('provenance',r.get('provenance',{})),('retrace_a2',r.get('retrace_a2',{})),('row',r)]:
    if obj.get('canonical'):fact(r,obj['canonical'],field+'.canonical')
    raster=obj.get('raster','');m=re.fullmatch(r'(scannet|scannetppv2|scannetpp|arkitscenes)__(.+)\.npz',raster)
    if m:fact(r,m[1]+'/'+m[2],field+'.raster')
   if r['qid'] in ids:
    assert r['qid'] not in found;found.add(r['qid']);f.write(raw+'\n');cells[r['pool']]+=1
 con.close();assert len(all_ids)==204413;assert found==ids;assert len(found)==17879
 assert all(len(v)==1 for v in aliases.values()),'ambiguous recorded canonical'
 # Collect every question-bearing JSON/JSONL/CSV in the kit and fixture tree.
 # This intentionally overincludes training fixtures, a conservative wording screen.
 corpus=collections.defaultdict(list); corpus_pins={};discovered=[]
 def walk(v,loc):
  if isinstance(v,dict):
   for k,x in v.items():
    if k.casefold() in ('question','question_text','prompt') and isinstance(x,str) and x.strip():corpus[x].append(loc)
    elif isinstance(x,(dict,list)):walk(x,loc)
  elif isinstance(v,list):
   for x in v:walk(x,loc)
 for root in [TREE,B/'fixtures']:
  for p in sorted(root.rglob('*')):
   if not p.is_file() or p.suffix not in ('.json','.jsonl','.csv'):continue
   discovered.append(str(p));before=sum(map(len,corpus.values()))
   try:
    if p.suffix=='.json':walk(json.loads(p.read_text()),str(p))
    elif p.suffix=='.jsonl':
     for l in p.open():
      if l.strip():walk(json.loads(l),str(p))
    else:
     for row in csv.DictReader(p.open()):walk(row,str(p))
   except (ValueError,UnicodeError):continue
   if sum(map(len,corpus.values()))>before:corpus_pins[str(p)]=sha(p)
 for name in ['COVERAGE_V2_PUB.tar','coverage_rows_v2.py','check_cov_v2.py','R1_M200_TRACE_ANALYSIS_20261119.md']:
  pins[name]={'path':str(out/name),'sha256':sha(out/name)}
 # Record all used kit source hashes, and verify them against its seal.
 sealed=json.loads(seal.read_text())['files']
 for package in ['student_pilot','generator/derivgen_v7/derivgen','trace_format']:
  for p in (TREE/package).glob('*.py'):
   rel=str(p.relative_to(TREE));digest=sha(p);assert sealed[rel]==digest,rel
   pins['kit:'+rel]={'path':str(p),'sha256':digest}
 digest_inputs={'store':PIN,'z.json':pins['z.json']['sha256'],'prepare_inputs.py':sha(Path(__file__))}
 dump(out/'scene_facts.json',{'input_sha256':digest_inputs,'facts':dict(aliases),'rule':'Recorded canonical or raster name; token must equal pinned BENCH v2 rung1 SHA256 rule; conflicting canonical identities fail.'})
 dump(out/'source_ids.json',{'input_sha256':digest_inputs,'ids':all_ids})
 dump(out/'wording_corpus.json',{'input_sha256':corpus_pins,'questions':dict(corpus),'searched_files':discovered,'scope':'All question/prompt fields in JSON/JSONL/CSV of sealed kit and fixtures; includes synthetic and training fixtures.'})
 for name in ['removed_rows.jsonl','scene_facts.json','source_ids.json','wording_corpus.json']:
  pins[name]={'path':str(out/name),'sha256':sha(out/name)}
 dump(out/'INPUTS.json',{'input_sha256':{k:v['sha256'] for k,v in pins.items()},'pins':pins,'tree':str(TREE),'tree_sha256':json.loads(seal.read_text())['tree_sha256'],'removed_rows':len(found),'source_cells':dict(cells),'prepare_script_sha256':sha(Path(__file__))})
 (ROOT/'STATUS.md').write_text('Inputs pinned: store v7 matches 210b2534; all 17,879 removal qids occur exactly once. W/w19 seal and used kit modules match their hashes. Scene facts derive only from recorded fields that reproduce the pinned scene-token formula. The converter and independent checks are next.\n')
 print(json.dumps({'removed':len(found),'source_cells':dict(cells),'scene_facts':len(aliases),'wordings':len(corpus),'wording_files':len(corpus_pins)}))
if __name__=='__main__':main()

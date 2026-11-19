"""Check reported counts, teaching references, artifact pins, and review-script adaptations."""
import collections as C, difflib, hashlib, json, pickle, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parent; B=Path('/scratch/jjyeung/orch_n30/sb_rowD7f'); O=B/'out'
def load(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
checks=load(O/'CHECKS.json'); report=(O/'FILTER_REPORT.md').read_text()
pins={}; pinbad=[]
for name in ('CHECKS.json','FILTER.json','RASTER_INDEX.json','VERIFY_FILTERED.json','LEAK_TEST.json','TEACHING_SET.json'):
 data=load(O/name)
 for p,value in data.get('input_sha256',{}).items():
  if not str(p).startswith('/scratch/'): continue
  expect=value if isinstance(value,str) else value.get('sha256')
  if expect is None: continue
  if p not in pins:pins[p]=sha(p) if Path(p).is_file() else 'MISSING'
  if pins[p]!=expect:pinbad.append([name,p,pins[p],expect])
sm=[json.loads(l) for l in open(O/'SOURCE_MAP.jsonl')];teach=load(O/'TEACHING_SET.json')
want={(m['source_qid'],m['source_i'],m['source_row_sha256']) for m in sm}
got={(m['qid'],m['store_i'],m['row_sha256']) for m in teach['existing_sources']}
assert want==got and len(teach['existing_sources'])==len(sm)
assert sha(teach['new_rows_pin']['path'])==teach['new_rows_pin']['sha256']
# Verify family-wide source identities and reported object counts against the frozen v7 census.
survey=load(B/'d7/out/SURVEY.json'); cen=pickle.load(open(ROOT/'work/census.pkl','rb'))['dirrows']
names=C.Counter();survbad=[]; seen=set()
for r in survey['rows']:
 i=r['i'];s=cen.get(i)
 if s is None or s['qid']!=r['qid'] or s['sha']!=r['source_sha256']:survbad.append(r['qid']);continue
 if any(n not in s['q'] for n in r['objects']):survbad.append(['name_not_in_question',r['qid']])
 names.update(n.strip().casefold() for n in r['objects']); seen.add(i)
# Inspect original-to-local review changes without Git.
diffs=[];source_hashes={}
for name in ('rev_census.py','rev_verify7.py','rev_rooms7.py','rev_leak7.py','rev_wording7.py','rev_fixcheck7.py'):
 old=Path('/scratch/jjyeung/orch_n30/sb_drev7')/name; new=ROOT/name
 source_hashes[str(old)]=sha(old);source_hashes[str(new)]=sha(new)
 diffs.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(old),tofile=str(new)))
(ROOT/'work/SCRIPT_ADAPTATIONS.diff').write_text(''.join(diffs))
# Producer machine reports must agree with the independent checks.
v=load(ROOT/'work/VERIFY_REVIEW.json');p=load(ROOT/'work/PILOT_REVIEW.json');r=load(ROOT/'work/ROOMS_REVIEW.json');w=load(ROOT/'work/WORDING_REVIEW.json')
fail=[]
if checks['checks']['field_diff']['fields']!=v['field_diff']:fail.append('field_diff')
if checks['checks']['exact_cell_counts']['filtered_cells']!={k.replace('|','/'):n for k,n in v['cells'].items()}:fail.append('cells')
if checks['checks']['filter']['dropped_pairs']!=p['results']['dropped']:fail.append('drop_count')
if checks['checks']['filter']['rows_out']!=p['results']['rows_out']:fail.append('rows_out')
if checks['checks']['blocker_B2_no_facing']['teaching_expected_draws']!=r['allocation']['v7_plus_twins_as_delivered(no_facing)']['teaching_pairs_expected_draws']:fail.append('draws')
if checks['checks']['wording_distance']['removed']!=len(w['hits']):fail.append('wording')
placeholder=set(load(O/'FILTER.json')['r1']['placeholder_labels'])
placeholder_rows=sum(any(n.strip().casefold() in placeholder for n in r['objects']) for r in survey['rows'])
out={'claim_mismatches':fail,'producer_input_pin_failures':pinbad,'teaching_reference_matches':len(want),'family_survey_rows':len(seen),'family_survey_matches_all_v7_directions':seen==set(cen),'family_survey_source_or_name_failures':survbad,'family_names':len(names),'family_placeholder_rows':placeholder_rows,'surface_bare_counts':{k:names[k] for k in ('wall','floor','ceiling')},'review_script_hashes':source_hashes,'scope_limits':['Raster visibility is unresolved for 7231 no-raster rows and 45 unmatched-name rows.','The binding artifact is not an implementation or approval of N build-22 store admission.','Clause balance applies to the teaching subset; the remaining v7 Step-1 population is toward-heavy.']}
(ROOT/'work/CLAIMS_REVIEW.json').write_text(json.dumps(out));print(json.dumps({k:v for k,v in out.items() if k!='review_script_hashes'},indent=1))

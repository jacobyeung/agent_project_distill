"""Census and mathematical options; never substitutes a model for native replay."""
import csv,gzip,json,hashlib,re,sys
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from parse_direction import parse
W=Path(__file__).resolve().parent;O=W/'out'
def pin(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return dict(path=str(p),sha256=h.hexdigest())
source=json.loads((O/'SOURCE_CENSUS.json').read_text())
inputs={i['path']:i for i in source['inputs']}
for p in [O/'SOURCE_CENSUS.json',O/'DIRECTION_ROWS.tsv.gz',W/'parse_direction.py',Path(__file__),O/'LOADER_BOUNDARY.json']:
 item=pin(p);inputs[item['path']]=item
rows=[]
with gzip.open(O/'DIRECTION_ROWS.tsv.gz','rt') as f:
 for r in csv.DictReader(f,delimiter='\t'):
  r.update(parse(r));rows.append(r)
assert len({r['qid'] for r in rows})==len(rows)
missing=Counter(k for r in rows for k in ('clause','difficulty','forward_relation','answer_side') if r[k]=='MISSING')
assert not missing,missing
assert all(r['facing']==r['clause'] for r in rows if r['facing'])
assert all(r['clause']=='away' for r in rows if r['source']=='twins')
assert all((r['forward_relation']=='behind')==(r['answer_side']==('back' if r['clause']=='toward' else 'front')) for r in rows if r['difficulty']=='hard')
byqid={r['qid']:r for r in rows}
back_sources={r['source_key'] for r in rows if r['source']=='twins' and r['difficulty']=='hard' and r['forward_relation']=='behind'}
flip={'left':'right','right':'left','front-left':'back-right','front-right':'back-left','back-left':'front-right','back-right':'front-left'}
for r in rows:
 if r['source']=='twins':
  parent=byqid[r['source_key']]
  assert r['forward_line']==parent['forward_line'],r['qid']
  assert r['answer_label']==flip[parent['answer_label']],r['qid']
assert all(q in byqid and byqid[q]['clause']=='toward' and byqid[q]['difficulty']=='hard' and byqid[q]['forward_relation']=='behind' for q in back_sources)
cell_draws={c['type']:int(Fraction(str(c['rows_per_step']))*1000) for c in source['card']['cells']}
assert cell_draws['direction']==36866 and cell_draws['facing_pairs']==18170
for c in source['card']['cells']:
 if c['stream']=='vqa':assert cell_draws[c['type']]<=4*source['families'].get(c['type'],0)
assert sum(cell_draws[c['type']] for c in source['card']['cells'] if c['stream']=='vqa')==128000
family_rows=Counter(r['family'] for r in rows)
TH=lambda r:r['clause']=='toward' and r['difficulty']=='hard'
fb={f:Counter(r['answer_side'] for r in rows if r['family']==f and TH(r)) for f in family_rows}
coeff={f:{'back':Fraction(sum(c.values()),2*c['back']),'front':Fraction(sum(c.values()),2*c['front'])} for f,c in fb.items()}
assert all(v<=4 for c in coeff.values() for v in c.values())
def weight(r,name):
 if name=='baseline':return Fraction(1)
 if name=='b_sources_twice':return Fraction(2 if r['qid'] in back_sources else 1)
 if name=='b_sources_cap4':return Fraction(4 if r['qid'] in back_sources else 1)
 if name in ('a_cap4','a_plus_b_cap4'):return Fraction(4 if TH(r) and r['forward_relation']=='behind' else 1)
 if name=='c_front_downweight' and TH(r) and r['answer_side']=='front':return Fraction(fb[r['family']]['back'],fb[r['family']]['front'])
 if name=='chosen_balance_preserve_mass' and TH(r):return coeff[r['family']][r['answer_side']]
 return Fraction(1)
def summary(weights):
 groups={}
 for r,w in zip(rows,weights):
  key=(r['clause'],r['difficulty'])
  g=groups.setdefault(key,dict(amount=0,answers=Counter(),answer_sides=Counter(),forward_relations=Counter()))
  g['amount']+=w;g['answers'][r['answer_label']]+=w;g['answer_sides'][r['answer_side']]+=w;g['forward_relations'][r['forward_relation']]+=w
 result=[]
 for (clause,difficulty),g in sorted(groups.items()):
  n=g['amount'];out=dict(clause=clause,difficulty=difficulty,amount=float(n))
  for field in ('answers','answer_sides','forward_relations'):
   out[field]={k:{'amount':float(v),'share':float(v/n)} for k,v in sorted(g[field].items())}
  result.append(out)
 return result
population_summary=summary([1]*len(rows));options={}
for name in ['baseline','a_cap4','b_sources_twice','b_sources_cap4','a_plus_b_cap4','c_front_downweight','chosen_balance_preserve_mass']:
 weights=[weight(r,name) for r in rows]
 mass=Counter()
 for r,w in zip(rows,weights):mass[r['family']]+=w
 density=[Fraction(cell_draws[r['family']])*w/mass[r['family']] for r,w in zip(rows,weights)]
 fixed_count=None
 if name in ('a_cap4','a_plus_b_cap4','b_sources_twice','b_sources_cap4'):
  fixed_count=2 if name=='b_sources_twice' else 4
  chosen_rows=[TH(r) and r['forward_relation']=='behind' if name in ('a_cap4','a_plus_b_cap4') else r['qid'] in back_sources for r in rows]
  fixed_by_family=Counter(r['family'] for r,selected in zip(rows,chosen_rows) if selected)
  residual={f:Fraction(cell_draws[f]-fixed_count*fixed_by_family[f],family_rows[f]-fixed_by_family[f]) for f in family_rows}
  assert all(v>=0 for v in residual.values())
  density=[Fraction(fixed_count) if selected else residual[r['family']] for r,selected in zip(rows,chosen_rows)]
 assert max(density)<=4
 for f in family_rows:assert sum(d for r,d in zip(rows,density) if r['family']==f)==cell_draws[f]
 groups=summary(density)
 options[name]=dict(status='ANALYTICAL_EXPECTATION_NOT_LOADER_OUTPUT',clause_difficulty=groups,
  total_draws_per_1000_steps=288000,vqa_draws_per_1000_steps=128000,
  direction_and_facing_draws_per_1000_steps=sum(cell_draws[f] for f in family_rows),
  card_cell_draws=cell_draws,card_cell_share={k:v/288000 for k,v in cell_draws.items()},
  normalization_mass={f:str(v) for f,v in mass.items()} if fixed_count is None else 'NOT_APPLICABLE: fixed actual draw counts for the selected rows; residual quota uniformly distributed within the cell',max_relative_weight=str(max(weights)) if fixed_count is None else None,fixed_actual_draws_for_selected_rows=fixed_count,max_expected_draws_per_row=float(max(density)),
  hard_per_row_cap_required=4,hard_cap_implemented=False,
  toward_hard_back_share=next(g['answer_sides']['back']['share'] for g in groups if (g['clause'],g['difficulty'])==('toward','hard')),
  away_hard_back_share=next(g['answer_sides']['back']['share'] for g in groups if (g['clause'],g['difficulty'])==('away','hard')))
base=options['baseline']
for name,o in options.items():
 for g,b in zip(o['clause_difficulty'],base['clause_difficulty']):
  g['draw_change_from_baseline']=g['amount']-b['amount']
  g['share_of_total_draws']=g['amount']/288000
  g['share_of_total_draws_change']=g['draw_change_from_baseline']/288000
 o['away_hard_not_above_71_8_percent']=o['away_hard_back_share']<=0.718
chosen=options['chosen_balance_preserve_mass']
assert abs(chosen['toward_hard_back_share']-.5)<1e-12
assert chosen['away_hard_back_share']<=base['away_hard_back_share']+1e-12
assert all(abs(g['draw_change_from_baseline'])<1e-9 for g in chosen['clause_difficulty'])
# Keep all unique source evidence; count native parser disagreements independently.
native_disagreement=Counter()
for r in rows:
 nc,nd,ns=json.loads(r['native_dimensions_json'])
 if nc!=r['clause']:native_disagreement[r['family']+'|'+nc+'->'+r['clause']]+=1
# Deterministic stratified hand-review sample, plus all alternate wording patterns.
selected=[];ids=set()
def add(r):
 if r['qid'] not in ids:ids.add(r['qid']);selected.append(r)
for key in sorted({(r['family'],r['clause'],r['difficulty'],r['answer_side']) for r in rows}):
 add(next(r for r in rows if (r['family'],r['clause'],r['difficulty'],r['answer_side'])==key))
for pattern in ['directed toward','oriented toward','gaze fixed','aiming toward','gazing at','turned toward','directing my view','viewing','next to me','opposite direction','with my back','turned away']:
 found=next((r for r in rows if pattern in r['question']),None)
 if found:add(found)
for key in sorted({(r['source'],r['clause'],r['difficulty'],r['answer_label']) for r in rows}):
 if len(selected)>=40:break
 add(next(r for r in rows if (r['source'],r['clause'],r['difficulty'],r['answer_label'])==key))
for r in sorted(rows,key=lambda r:hashlib.sha256(r['qid'].encode()).hexdigest()):
 if len(selected)>=40:break
 add(r)
assert len(selected)==40
lines=['# Forty direction rows for manual parser validation','', 'These are source text checks, not visual ground-truth checks. Full source hashes are in SOURCE_CENSUS.json.','']
for i,r in enumerate(selected,1):
 lines.extend([f"## {i}. {r['qid']}",f"Source: {r['source']}[{r['source_i']}]; cell: {r['family']}; row SHA256: `{r['row_sha256']}`.",f"Question: {r['question'].replace(chr(10),' ')}",f"Forward trace: {r['forward_line']}",f"Options: {r['options_json']}; selected answer: {r['answer']}.",f"Parsed: {r['clause']} / {r['difficulty']} / {r['forward_relation']} / {r['answer_label']}.",''])
(O/'READ40.md').write_text('\n'.join(lines)+'\n')
with (O/'READ40_KEYS.tsv').open('w') as f:
 writer=csv.writer(f,delimiter='\t');writer.writerow(['number','qid','clause','difficulty','forward_relation','answer_label'])
 for i,r in enumerate(selected,1):writer.writerow([i,r['qid'],*[r[k] for k in ('clause','difficulty','forward_relation','answer_label')]])
# Snapshot every direction row's parsed dimensions and source identity.
with gzip.open(O/'PARSED_ROWS.tsv.gz','wt') as f:
 fields=['qid','source','source_i','row_sha256','family','clause','difficulty','forward_relation','answer_label','answer_side','source_key']
 writer=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore');writer.writeheader();writer.writerows(rows)
result=dict(status='SOURCE_CENSUS_COMPLETE_NATIVE_REPLAY_MISSING',inputs=list(inputs.values()),tree_seal=source['tree_seal'],
 source_counts=source['counts'],card_cell_eligible=source['families'],direction_row_count=len(rows),direction_card_cells=dict(family_rows),
 before_from_loader='MISSING',after_from_loader='MISSING',native_error=json.loads((O/'LOADER_BOUNDARY.json').read_text())['native_error'],
 source_population=population_summary,expected_before=base,
 expectations_basis='Expected inclusion under the native uniform-within-cell rule, before deterministic seed realization; full card quotas assumed feasible for non-VQA streams. No production proof or offset mapping is fabricated.',
 analytical_options=options,chosen_option='chosen_balance_preserve_mass',chosen_relative_weights={f:{s:str(v) for s,v in c.items()} for f,c in coeff.items()},
 back_relation_hard_twin_sources=len(back_sources),parser_missing=dict(missing),native_clause_disagreements=dict(native_disagreement),
 exclusions_scope='All 12 bound removal lists, source-room authority with pinned tiered aliases, native dev/benchmark scenes, held QIDs, wording, text, and R0 reserve checks. Six relative-distance text failures are counted as failures, not silently admitted. No images or model were loaded.',
 all_non_direction_cells_unchanged=True,
 warnings=['The production audit reports only the direction card cell and omits facing_pairs.', 'The native clause parser misses alternate toward/away clauses.', 'Per-row finite draw schedules and hard-cap enforcement need a tree change; modeled shares are not realized loader draws.'])
(O/'CENSUS.json').write_text(json.dumps(result,indent=2)+'\n')
print('ROW COUNTS',len(rows),dict(family_rows),'source_twins_behind',len(back_sources),'weights',result['chosen_relative_weights'])
for g in population_summary:print('POP',g['clause'],g['difficulty'],g['amount'],g['answer_sides'])
for name,o in options.items():print('OPTION',name,o['toward_hard_back_share'],o['away_hard_back_share'],o['max_expected_draws_per_row'])
print('Native discrepancies',native_disagreement)
(W/'STATUS.md').write_text('Stage 3: Parsed every eligible direction and facing-pair row and generated the 40-row review sample. Compared ceiling-bounded analytical options using N’s distinct card-cell draw rates. The selected mass-preserving reweighting targets 50% toward-hard back answers and preserves all other clause/difficulty totals. Native before/after replay remains MISSING because the actual launch population is incomplete and the sampler has no per-row weighting interface; no tree changes were made.\n')

import json,sqlite3,hashlib,collections,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent
zpath=pathlib.Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/z.json');z=zpath.read_bytes();ids={r['row_key'] for l in z.splitlines() if (r:=json.loads(l))['reason']=='count_diag_first_seen_list_form'}
base=pathlib.Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7');ranges=json.load(open(base/'FAMILY_INDEX_RANGES.json'))['families']['object_counting']
c=sqlite3.connect('file:'+str(base/'vqa/rows.sqlite')+'?mode=ro',uri=True);counts=collections.Counter();examples={};n=0
with open(ROOT/'in/count_sources.jsonl','w') as out:
 for lo,hi in ranges:
  for i,raw in c.execute('select i,row from rows where i between ? and ?',(lo,hi)):
   r=json.loads(raw)
   if r['qid'] not in ids:continue
   out.write(raw+'\n');n+=1;key=(r.get('pool'),r['provenance'].get('count_kind'));counts[str(key)]+=1
   if key not in examples:examples[key]=r
print('extracted',n,'removal_ids',len(ids),'kinds',counts)
for k,r in examples.items():
 print('\nEXAMPLE',k,'KEYS',list(r));print('Q',r['student_input']['question']);print('T',r['target']);print('PROV',str(r['provenance'])[:3500])
(ROOT/'STATUS.md').write_text('Source discovery is complete on trinity-1-18. The local store supplies removed counting rows and the w19 tree supplies the current sealed validation code. Relative count uses option-letter answers. Tally compatibility with the native direct-trace grammar remains under test. No training, network, or GPU work has run.\n')

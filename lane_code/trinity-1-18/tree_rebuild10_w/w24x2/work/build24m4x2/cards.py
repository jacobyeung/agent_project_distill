from pathlib import Path
import sys,json,gzip,re,collections
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4x2';sys.path[:0]=[str(D),str(L/'out/rcj'),str(L/'work/tree_r1c')]
from seal import write,z
import ch
from student_pilot.p3_provenance import file_pin
rd=json.loads(gzip.decompress((D/'published/rd0/rdiff.json.gz').read_bytes()))
receipt=z.load(D/'c072905b.json');entries=receipt['rows'];names=z.load(D/'SOURCES.json')['names']
n=[x for x in rd['N'] if x['key'][3] in names and not x['key'][2].startswith('a0_')]
p={x['key'][2] for x in rd['N']+rd['P_absent'] if x['key'][3] in names}
assert len(n)==10945 and len(p)==12475
v1=[x for x in n if x['key'][0]=='d2' and x['key'][3] in ('T1H1_gen_r2','T1H2_gen_r2')]
distance=z.load(D/'published/materialization.json')['types']['object_abs_distance']['pool_program_rows']
norm=lambda q:re.search(r'vsi590k_[0-9]+',q).group() if re.search(r'vsi590k_[0-9]+',q) else q
normalized={norm(q) for q in entries}
repaired={norm(q) for q,e in entries.items() if e.get('repair_sha256')}
flagged={norm(q) for q,e in entries.items() if any(s!='full' for s in e.get('box_statuses',[]))}
exact=p&entries.keys()
rows=[json.loads(x['row']) for x in z.load(D/'published/p_sample.json')['rows']]
provenance=[]
for r in rows:
 source=r.get('s1_source',{});canonical=source.get('provenance',{}).get('canonical')
 if source.get('name') in ('T1H1_gen_r2','T1H2_gen_r2') and r['dataset']=='d2':
  assert canonical.startswith('scannetpp/');provenance.append(dict(qid=r['qid'],source=source['name'],canonical=canonical))
value=dict(status='PASS',receipt_sha256=z.sha(D/'c072905b.json'),
 sources={f:z.sha(D/'published'/f) for f in ('rd0/rdiff.json.gz','materialization.json','p_sample.json','chain.json')},
 n_routing_rows=len(rd['N']),exempted_pool_rows=len(n),still_checked_rows=len(rd['N'])-len(n),
 source_counts=dict(collections.Counter(x['key'][3] for x in n)),
 exempted_v1_rows=len(v1),distance_rows=distance,v1_distance_fraction=len(v1)/distance,
 v1_classification='Published d2 rows from T1H1_gen_r2/T1H2_gen_r2; source-family classification corroborated by all available published canonical provenance. CPU job checks canonical provenance on every real row.',
 v1_published_provenance=provenance,p_pool_qids=len(p),exact_matches=len(exact),
 exact_repaired=sum(bool(entries[q].get('repair_sha256')) for q in exact),
 exact_flagged=sum(any(s!='full' for s in entries[q]['box_statuses']) for q in exact),
 normalized_qid_matches=sum(norm(q) in normalized for q in p),normalized_distinct_matches=len({norm(q) for q in p}&normalized),
 normalized_repaired=sum(norm(q) in repaired for q in p),normalized_flagged=sum(norm(q) in flagged for q in p),
 normalization='Regex vsi590k_[0-9]+ on both sides, including a0_, x2 and dh variants; diagnostic only. 7,232 is exact QID membership, not this normalized count.',
 scope='Offline complete published keys and receipt entries; no fabricated row digests or audit statuses.')
assert (len(v1),distance,len(exact))==(3362,11663,7232)
write(D/'CARD_NUMBERS.json',value)
cfg=dict(extent_receipt=file_pin(D/'c072905b.json'),r1_training=dict(extent_pool_sources=names))
native_sample=ch.card_rows(cfg,iter(rows),iter(rows));write(D/'CARD_SAMPLE_TEST.json',dict(status='PASS',scope='Actual published sample, not full DB',result=native_sample))
assert native_sample['counts']['exempted_rows']==14 and native_sample['counts']['v1_rows']==len(provenance)
print(json.dumps({k:v for k,v in value.items() if k not in ('sources','v1_published_provenance','scope')},indent=2))

"""Artifact chronology, archive identity, and local K1 cache provenance."""
import collections, datetime, hashlib, json, tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SRC=ROOT.parent/'sb_mask_phrase'
PINS={}
def read(p):
    p=Path(p); b=p.read_bytes(); PINS[str(p)]=hashlib.sha256(b).hexdigest(); return b
def js(p): return json.loads(read(p))
def stamp(p):
    s=p.stat()
    return dict(mtime_utc=datetime.datetime.fromtimestamp(s.st_mtime,datetime.timezone.utc).isoformat(),mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,bytes=s.st_size)
def main():
    read(__file__); read(ROOT/'run_review.sh')
    for p in [ROOT.parent/'sb_mdrev/REVIEW_VERDICT.md',ROOT.parent/'sb_mdrev2/REVIEW_VERDICT.md',
              ROOT.parent/'sb_cachefix/out/CACHEFIX_REPORT.md']:
        read(p)
    decision=js(SRC/'out/DECISION.json'); bars=js(SRC/'out/BARS.json')
    paths=['PROMPT.md','in/v2/KIT_SPEC_mask_phrase.md','in/v3/KIT_SPEC_mask_phrase_v2.md',
           'out/BARS.json','work/BARS.sha256','out/DECISION.json','out/PHRASE_SET.json','out/PHRASE_FOLDS.json',
           'out/PER_ITEM.jsonl','out/OBJECTS.json','out/TESTS.json','out/DRYRUN.json','out/PHRASE_REPORT.md',
           'work/stale_v1_out/DECISION.json','work/stale_v1_out/PER_ITEM.jsonl',
           'HANDOFF_STOPPED_SESSION.md','cursor.log','cursor_stopped_1008Z.log']
    stamps={}
    for name in paths:
        p=SRC/name;read(p);stamps[name]=stamp(p)
    governing={p:hashlib.sha256(read(SRC/p)).hexdigest()==h for p,h in bars['governing_sha256'].items()}
    archive=SRC/'out/sb_mask_phrase.tar';read(archive)
    members={}; different=[]; absent=[]
    with tarfile.open(archive) as tar:
        for m in tar.getmembers():
            if not m.isfile():continue
            h=hashlib.sha256(tar.extractfile(m).read()).hexdigest()
            members[m.name]=h
            parts=Path(m.name).parts
            candidates=[SRC/Path(*parts),SRC/Path(*parts[1:])]
            match=next((p for p in candidates if p.is_file()),None)
            if match is None:absent.append(m.name)
            elif hashlib.sha256(read(match)).hexdigest()!=h:different.append(m.name)
    vendor=ROOT.parent/'k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam'
    for n in ['variantlib.py','variant_cache.py','vendor/sam_backend.py']:
        read(vendor/n)
    manifest=js(ROOT.parent/'sb_kbox4/pinned_train.json')
    ids=set(read('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt').decode().splitlines())
    caps=[c for c in manifest['captures'] if any(r['id'] in ids for r in c['rows'])]
    contracts=collections.Counter(); stubs=0; pin_bad=[]; receipts_bad=[]; radiator=[]; tower_bad=[]; producer_bad=[]
    raw_pres_bad=0; alias_missing_pres=0; alias_mixed_frames=0
    for c in caps:
        key=hashlib.sha256(json.dumps(c['canonical'],sort_keys=True,allow_nan=False).encode()).hexdigest()[:16]
        p=Path('/scratch/jjyeung/k1/run_convert_2')/key/'candidates.json'
        cache=js(p);receipt=js(p.parent/'CACHE_COMPLETE.json')
        towerreceipt=js(Path('/scratch/jjyeung/k1/run_tower_sam_2')/key/'PHASE_COMPLETE.json')
        if towerreceipt['files']['candidates.json']!=PINS[str(p)]:tower_bad.append(str(p))
        for src in ['variantlib.py','variant_cache.py','vendor/sam_backend.py']:
            source=str(vendor/src)
            if receipt['sources'].get(source)!=PINS[source]:producer_bad.append((str(p),source))
        contracts[cache['contract']['prompts']]+=1;stubs+=bool(cache['stub'])
        if decision['input_sha256'].get(str(p))!=PINS[str(p)]:pin_bad.append(str(p))
        if receipt['files']['candidates.json']['sha256']!=PINS[str(p)]:receipts_bad.append(str(p))
        for slot,frame in cache['frames'].items():
            for n,rec in frame['phrases'].items():
                pres={}
                for x in rec['instances']:
                    prompt=x.get('source_prompt',n)
                    if prompt==n and x.get('source_presence',rec['presence'])!=rec['presence']:raw_pres_bad+=1
                    if prompt!=n and 'source_presence' not in x:alias_missing_pres+=1
                    pres.setdefault(prompt,set()).add(x.get('source_presence',rec['presence']))
                    if n=='heater' and prompt=='radiator':
                        radiator.append(dict(capture=c['canonical'],slot=slot,query=x['query'],source_query=x.get('source_query'),
                                             score=x['score'],presence=x['source_presence'],source_tile=x.get('source_tile'),
                                             mask_sha256=hashlib.sha256(json.dumps(x['mask'],sort_keys=True).encode()).hexdigest()))
                alias_mixed_frames+=sum(len(v)>1 for v in pres.values())
    out=dict(command='bash run_review.sh audit_static.py',timestamps=stamps,governing_hashes_match=governing,
             bars_sha256=PINS[str(SRC/'out/BARS.json')],decision_bars_sha256=decision['bars_file']['sha256'],
             written_before_any_score_claim=bars['written_before_any_score'],
             stale_scores_precede_bars=stamps['work/stale_v1_out/PER_ITEM.jsonl']['mtime_ns']<stamps['out/BARS.json']['mtime_ns'],
             archive=dict(sha256=PINS[str(archive)],files=len(members),different=different,absent=absent,member_sha256=members),
             cache=dict(captures=len(caps),contracts=dict(contracts),stubs=stubs,decision_pin_mismatches=pin_bad,
                        receipt_pin_mismatches=receipts_bad,raw_presence_mismatches=raw_pres_bad,
                        tower_receipt_mismatches=tower_bad,producer_source_pin_mismatches=producer_bad,
                        missing_alias_presence=alias_missing_pres,mixed_within_prompt_frames=alias_mixed_frames,
                        radiator_proposals=len(radiator),radiator_captures=len({r['capture'] for r in radiator}),
                        radiator_source_queries_missing=sum(r['source_query'] is None for r in radiator),
                        radiator_tiled=sum(r['source_tile'] is not None for r in radiator)),radiator=radiator,
             input_sha256=PINS)
    (ROOT/'STATIC_AUDIT.json').write_text(json.dumps(out,indent=1)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['input_sha256','radiator','archive','timestamps']},indent=1))
    print('archive',out['archive']['sha256'],len(members),'different',different,'absent',absent)
if __name__=='__main__':main()

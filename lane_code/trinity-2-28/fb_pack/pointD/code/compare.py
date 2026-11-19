"""Compare all real target bytes and native fixture rebuilds without inventing GT assets."""
import hashlib, importlib.util, json, os, resource, sqlite3, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT.parent
TREE = ROOT/'work/new'
sys.path.insert(0, str(TREE))
resource.setrlimit(resource.RLIMIT_AS, (38*1024**3, 38*1024**3))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''): h.update(block)
    return h.hexdigest()
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value
def connect(path): return sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
import torch
torch.set_num_threads(16)
from student_pilot import carrier_c1_data as new, pointing_locate as locate
from student_pilot.p3_provenance import file_pin
from tests.test_pointing_locate import fixture, saved
old = module('student_pilot._base_carrier_data', ROOT/'work/base/student_pilot/carrier_c1_data.py')
reference_path=PACK/'point/code/pointing_locate.py'
reference=module('fbp_point_reference',reference_path)
assert sha(reference_path)==locate.RULE['source_sha256']
source=PACK/'in/pointing/rows_c09bb5ca.sqlite'
target=PACK/'point/out/rows_pointing_locate.sqlite'
assert sha(source)=='c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938'
assert sha(target)=='d5362229ca7f6d6be7cb051c89bd096b5c7973658da4399b63c3ba6e88c042e0'
inputs={str(p):sha(p) for p in (source,target,reference_path,Path(__file__),ROOT/'out/SETUP.json')}
counts=Counter(); samples={}; first=None
with connect(source) as a, connect(target) as b:
    for (i,raw,aux),(j,refraw,refaux) in zip(a.execute('SELECT * FROM rows ORDER BY i'),
                                           b.execute('SELECT * FROM rows ORDER BY i'),strict=True):
        row, expected=json.loads(raw),json.loads(refraw)
        if first is None:first=row
        answer=row['target'].split('</think>\n\n')[1]
        transformed=locate.render(row,answer)
        assert i==j and aux==refaux
        assert transformed==expected['target']==reference.transformed(row)[0]
        assert transformed.split('</think>\n\n')[1].encode()==answer.encode()
        assert expected=={**row,'target':transformed}
        locate.assert_target(expected)
        # Exercise weighting across real labels/indices with a deterministic character tokenizer.
        labels=torch.tensor([[-100,*map(ord,transformed),-100]])
        weights=new.pointing_token_weights(labels,chr,pointing_locate=locate.RULE_PIN)
        k=int(weights.argmax())
        absent=row['pointing']['kind']=='gt_absent'
        assert chr(int(labels[0,k]))==(':' if absent else '.')
        assert k==1+locate.decision_offset(transformed)
        counts['rows']+=1; counts['null' if absent else 'visible']+=1
        counts['answer_bytes_identical']+=1; counts['targets_equal_reference']+=1
        counts['decision_position_checked']+=1
        if ('null' if absent else 'visible') not in samples:
            samples['null' if absent else 'visible']=dict(i=i,qid=row['qid'],target=transformed,
                tokenizer='deterministic character fixture; not the production tokenizer',
                chosen_token=chr(int(labels[0,k])), token_index_in_labels=k,
                normalized_decision_weight=float(weights[0,k]),
                supervised_mean=float(weights[labels!=-100].mean()))
assert counts['rows']==25020
root=ROOT/'work/comparison'; root.mkdir()
rows, fixture_source, division=fixture(root)
inputs[fixture_source['path']]=fixture_source['sha256'];inputs[division['path']]=division['sha256']
for pin in [rows[0]['pointing']['mask'],*rows[0]['student_input']['frames']]:inputs[pin['path']]=pin['sha256']
fixtures=[]
for filtered in (False,True):
    receipts={}
    for name,mod in (('base',old),('new',new)):
        receipts[name]=mod.build_stream(fixture_source,division,root/f'{name}_{filtered}','pointing',
            ground_target_filter=filtered)
    assert receipts['base']['database']['sha256']==receipts['new']['database']['sha256']
    marked=new.build_stream(fixture_source,division,root/f'locate_{filtered}','pointing',
        ground_target_filter=filtered,pointing_locate=locate.RULE_PIN)
    for before,after in zip(saved(receipts['base']),saved(marked),strict=True):
        answer=before['target'].split('</think>\n\n')[1]
        assert after['target']==reference.transformed({**before,'target':new.READOUT_TARGET+answer})[0]
        assert after=={**before,'target':after['target']}
    locate.assert_store(marked,locate.RULE_PIN)
    fixtures.append(dict(ground_target_filter=filtered, rows=marked['count'],
        absent_rule_database_sha256=receipts['base']['database']['sha256'],
        field_absent_byte_identical=True, field_present_targets_equal_reference=True,
        mask_json_bytes_unchanged=True, receipt=marked))
for name,mod in (('base',old),('new',new)):
    receipts[name]=mod.build_stream(file_pin(root/'base_True/receipt.json'),division,
        root/f'receipt_{name}','pointing',source_receipt=True,ground_target_filter=True)
assert receipts['base']['database']['sha256']==receipts['new']['database']['sha256']
fixture_receipt_rebuild=dict(rows=receipts['base']['count'],field_absent_byte_identical=True,
    sha256=receipts['base']['database']['sha256'])
receipt_path=PACK/'ro/orch_n30/tree_rebuild10_w/ext/preceipts/rc3/pool_7c9f2d84_receipt.json'
inputs[str(receipt_path)]=sha(receipt_path)
source_receipt=json.loads(receipt_path.read_text())
division_local=PACK/'ro/orch_n30/tree_rebuild10_w/ext/preceipts/rc3/u/ap/f02f16ad/s/a3v2/division.json'
assert sha(division_local)==source_receipt['division']['sha256']
inputs[str(division_local)]=sha(division_local)
missing=[dict(input=first['pointing']['mask'],expected_location=first['pointing']['mask']['path'],
              status='MISSING',reason='No local GT-mask staging map or asset is supplied; NFS access prohibited.'),
         dict(input=first['student_input']['frames'][0],expected_location=first['student_input']['frames'][0]['path'],
              status='MISSING',reason='No supplied local match; exact basename absent under /scratch/jjyeung/k1_frames and the named ext copy.')]
for name,mod in tuple(sys.modules.items()):
    path=getattr(mod,'__file__',None)
    if path and Path(path).is_file() and Path(path).is_relative_to(ROOT/'work'):
        inputs[path]=sha(path)
inputs[str(ROOT/'work/base/student_pilot/carrier_c1_data.py')]=sha(ROOT/'work/base/student_pilot/carrier_c1_data.py')
record=dict(command='bash code/run.sh compare',input_sha256=inputs,rule_pin=locate.RULE_PIN,
    real_stored_targets=dict(status='PASS',counts=dict(counts),samples=samples,
        scope='All real rows: exact target transform and decision position; GT masks were not recomputed.'),
    native_build_stream_fixtures=dict(status='PASS',runs=fixtures,source_receipt_rebuild=fixture_receipt_rebuild),
    real_build_stream=dict(status='MISSING',first_required_inputs=missing,
        scope='No real source row claimed as rebuilt. The native sample consists of four synthetic rows, three after shape filtering.'),
    production_tokenizer=dict(status='MISSING',expected_location='No production tokenizer path supplied',
        scope='Tests cover character tokens, separate punctuation and merged frame/punctuation tokens.'))
(ROOT/'out/COMPARE.json').write_text(json.dumps(record,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Stage 3: All 25,020 real stored targets match the delivered Locate store exactly, with identical JSON answer bytes and correct decision positions under a character tokenizer. Native four-row fixture builds (three retained after shape filtering) preserve byte-identical SQLite stores when the field is absent, including receipt rebuilds. A full real-mask rebuild is MISSING because its GT-mask/RGB assets are not locally staged. Both full CPU suites are running.\n')
print(json.dumps(dict(real_counts=dict(counts),fixture_runs=len(fixtures),status='PASS_WITH_MISSING_REAL_REBUILD')))

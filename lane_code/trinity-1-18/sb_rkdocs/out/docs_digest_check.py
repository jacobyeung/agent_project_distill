"""Compare the copied kit's code and frozen files with its source receipts."""
import json
from pathlib import Path
from common import W, read, sha, write
SOURCE=Path('/scratch/jjyeung/orch_n30/sb_rkfix2')
before_tests=read(W/'out/docs_baseline/TESTS.json')
after_tests=read(W/'out/TESTS.json')
before_go=read(W/'out/docs_baseline/GO.template.json')
after_go=read(W/'configs/GO.template.json')

def code_inputs(record):
    result={}
    for name,h in record['input_sha256'].items():
        p=Path(name)
        for root in [SOURCE,W]:
            if p.is_relative_to(root):
                rel=p.relative_to(root)
                if rel.parts[0] in ['scripts','vendor','tests'] and p.suffix in ['.py','.sh']:
                    if str(rel) in result:assert result[str(rel)]==h
                    result[str(rel)]=h
                break
    return result

bt,at,bg,ag=map(code_inputs,[before_tests,after_tests,before_go,after_go])
assert bt==at and bg==ag
assert before_go==after_go
inputs={}
originals={**bt,**bg}
for rel,h in originals.items():
    for root in [SOURCE,W]:
        p=root/rel
        assert sha(p)==h, str(p)
        inputs[str(p)]=h
all_original_code={}
for directory in ['scripts','vendor','tests','evidence','review','out']:
    for p in (SOURCE/directory).rglob('*'):
        if p.is_file() and p.suffix in ['.py','.sh'] and '__pycache__' not in p.parts:
            rel=p.relative_to(SOURCE);h=sha(p)
            assert sha(W/rel)==h,str(rel)
            all_original_code[str(rel)]=h
            inputs[str(p)]=h;inputs[str(W/rel)]=h
frozen=['configs/KERNEL_PROVENANCE.json','configs/KERNEL_FROZEN.json']
for rel in frozen:
    assert sha(SOURCE/rel)==sha(W/rel)
    inputs[str(SOURCE/rel)]=sha(SOURCE/rel);inputs[str(W/rel)]=sha(W/rel)
for p in [W/'out/docs_baseline/TESTS.json',W/'out/docs_baseline/GO.template.json',
          W/'out/TESTS.json',W/'configs/GO.template.json',Path(__file__)]:inputs[str(p)]=sha(p)
assert after_tests['verdict']=='PASS' and after_tests['tests']==44
record=dict(verdict='PASS',code_files_checked=len(originals),all_original_code_files_checked=len(all_original_code),
            tests_code_input_digests_unchanged=True,go_code_input_digests_unchanged=True,
            go_template_bytes_unchanged=sha(W/'out/docs_baseline/GO.template.json')==sha(W/'configs/GO.template.json'),
            go_code_sha256_before=before_go['code_sha256'],go_code_sha256_after=after_go['code_sha256'],
            tests_file_sha256_before=sha(W/'out/docs_baseline/TESTS.json'),tests_file_sha256_after=sha(W/'out/TESTS.json'),
            frozen_records_unchanged=True,
            note='TESTS.json was regenerated with relocated input paths and the verification wrapper hash. The unchanged GO template retains source-root path identity; generate a fresh NOT_GO template at the launch root as OPERATOR directs.',
            command='bash scripts/cpu.sh out/docs_digest_check.py')
write(W/'out/DOCS_DIGESTS.json',record,inputs)
print('PASS:',len(originals),'original code files unchanged; TESTS/GO code input digests match; GO template and frozen records unchanged')

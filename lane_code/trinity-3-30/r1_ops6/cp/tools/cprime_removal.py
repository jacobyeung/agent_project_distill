"""Pool-only anonymization; preserve every byte outside each pool JSON string."""
import hashlib,json,re
from rebind import ROOT,write
SOURCE=__import__('pathlib').Path('/scratch/jjyeung/orch_n30/r1_ops6/cf/final_evidence/COUNT_FIX_REMOVE_B1.jsonl')
ORIGINAL='25c3db82b4c590a39924b6b9636b7b4372cf91134a6242fe9895daaca179ceba'
PATTERN=re.compile(rb'("pool"\s*:\s*)("(?:[^"\\]|\\.)*")')

def transform(raw):
    assert hashlib.sha256(raw).hexdigest()==ORIGINAL
    mapping={};result=[]
    for line in raw.splitlines(keepends=True):
        row=json.loads(line);pool=row['pool']
        token='p'+hashlib.sha256(pool.encode()).hexdigest()[:8]
        mapping[pool]=token
        matches=list(PATTERN.finditer(line));assert len(matches)==1
        match=matches[0];assert json.loads(match[2])==pool
        changed=line[:match.start(2)]+json.dumps(token).encode()+line[match.end(2):]
        expected={**row,'pool':token};assert json.loads(changed)==expected
        result.append(changed)
    assert len(set(mapping.values()))==len(mapping)
    return b''.join(result),mapping

def build():
    raw,mapping=transform(SOURCE.read_bytes());h=hashlib.sha256(raw).hexdigest()
    (ROOT/'out/records/z.json').write_bytes(raw)
    write(ROOT/'out/B1R_MAPPING.json',dict(original_sha256=ORIGINAL,sha256=h,pool_mapping=mapping,
        rows=len(raw.splitlines()),loader_evidence='work/tree/student_pilot/row_removals.py:27-46 validates row_key and optional defects; :48-61 matches keys only; pool is never accessed',
        scope='TRINITY ONLY; excluded from archive and operator kit'))
    return raw

if __name__=='__main__':print(hashlib.sha256(build()).hexdigest())

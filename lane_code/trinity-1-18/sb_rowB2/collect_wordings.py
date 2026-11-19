"""Collect local held-out wording for exclusion only; never render from it."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import unicodedata
from collections import defaultdict

ROOT=Path(__file__).resolve().parent
def norm(x):
    return ' '.join(unicodedata.normalize('NFKC', x).casefold().split())
def questions(x):
    if isinstance(x,dict):
        for k,v in x.items():
            if k in ('question','question_text','prompt') and isinstance(v,str) and v.strip() and (k!='prompt' or '?' in v):
                yield norm(v)
            elif isinstance(v,(dict,list)):
                yield from questions(v)
    elif isinstance(x,list):
        for v in x: yield from questions(v)
def main():
    pins, corpus, counts, failures = {}, set(), {}, []
    def add(name,data):
        pins[name]=hashlib.sha256(data).hexdigest()
        try:
            raw=gzip.decompress(data) if name.endswith('.gz') else data
            try: parsed=json.loads(raw)
            except json.JSONDecodeError: parsed=[json.loads(l) for l in raw.splitlines() if l.strip()]
            qs=list(questions(parsed)); corpus.update(qs); counts[name]=len(qs)
        except (ValueError,UnicodeDecodeError) as e:
            failures.append(dict(path=name,error=str(e)))
    for s in (ROOT/'inputs/wording_paths.txt').read_text().splitlines():
        p=Path(s)
        if p.suffix in ('.json','.jsonl'):
            add(str(p),p.read_bytes())
    grouped=defaultdict(list)
    for archive,member,size in json.loads((ROOT/'inputs/archive_wording_candidates.json').read_text()):
        grouped[archive].append(member)
    for archive,names in grouped.items():
        print('Wording corpus',Path(archive).name,len(names),flush=True)
        with tarfile.open(archive) as t:
            for name in names: add(archive+'::'+name,t.extractfile(name).read())
    result=dict(input_sha256=pins,questions=sorted(corpus),question_counts=counts,parse_failures=failures,
                use='exclusion-only',normalization='NFKC, casefold, collapsed whitespace')
    (ROOT/'inputs/WORDING_CORPUS.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Unique held-out questions',len(corpus),'parse failures',len(failures),flush=True)
if __name__=='__main__':main()

"""Collect available dev and benchmark questions for exclusion-only comparisons."""
import csv, hashlib, io, json
from pathlib import Path
BASE=Path(__file__).resolve().parent

def extract(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k.lower() in ('question','question_text','prompt','query','template') and isinstance(v,str) and v.strip():
                yield v
            elif isinstance(v,(dict,list)):
                yield from extract(v)
    elif isinstance(value,list):
        for v in value:yield from extract(v)

def main():
    paths=set(Path(x) for x in (BASE/'wording_paths.txt').read_text().splitlines())
    mirror=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/vsti_rel_dev_r0')
    paths.update([mirror/'items.jsonl',mirror/'R0DEV_VSTI_QUESTIONS.jsonl'])
    pins={str(p):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
          for p in (BASE/'wording_corpus.py',BASE/'wording_paths.txt')};words={};files=[];seen={}
    for p in sorted(paths):
        raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();pins[str(p)]=dict(sha256=h,bytes=len(raw))
        if h in seen:
            files.append(dict(path=str(p),duplicate_content_of=seen[h]));continue
        seen[h]=str(p)
        if p.suffix=='.csv':value=list(csv.DictReader(io.StringIO(raw.decode())))
        elif p.suffix=='.jsonl':value=[json.loads(x) for x in raw.splitlines() if x.strip()]
        else:value=json.loads(raw)
        found=list(extract(value));files.append(dict(path=str(p),wordings=len(found)))
        for w in found:words.setdefault(w,[]).append(str(p))
    value=dict(command='PYTHONDONTWRITEBYTECODE=1 python wording_corpus.py',input_sha256=pins,
        discovery='rg --files tree_rebuild10_w, filename filter recorded in wording_paths.txt; plus both local R0-dev question/item files',
        files=files,wordings=[dict(text=k,sources=v) for k,v in sorted(words.items())],
        limitation='Available local item and fixture wording only; no claim of complete external benchmark corpora.')
    (BASE/'out/WORDING_CORPUS.json').write_text(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(files),unique_files=len(seen),wordings=len(words))))

if __name__=='__main__':main()

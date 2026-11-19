#!/usr/bin/env -S nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B
"""Print all changed leaf paths; reject fields outside PREP_FIELDS.json."""
from pathlib import Path
import json,sys

MISSING=object()

def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for key in sorted(set(a)|set(b)):
            yield from differences(a.get(key,MISSING),b.get(key,MISSING),path+'.'+key if path else key)
    elif a is MISSING and isinstance(b,dict) or b is MISSING and isinstance(a,dict):
        value=b if a is MISSING else a
        if not value:yield path
        for key in sorted(value):
            yield from differences(MISSING,value[key],path+'.'+key)
    elif isinstance(a,list) and isinstance(b,list):
        for i in range(max(len(a),len(b))):
            yield from differences(a[i] if i<len(a) else MISSING,b[i] if i<len(b) else MISSING,path+'.'+str(i))
    elif a!=b:
        yield path

def main():
    if len(sys.argv)!=3:raise SystemExit('usage: prep_diff.py <pre.json> <v.json>')
    fields=json.loads(Path(__file__).with_name('PREP_FIELDS.json').read_text())['fields']
    paths=list(differences(*(json.loads(Path(p).read_text()) for p in sys.argv[1:])))
    for p in paths:print(p+(' OUTSIDE_ALLOWLIST' if p not in fields else ''))
    return int(any(p not in fields for p in paths))

if __name__=='__main__':raise SystemExit(main())

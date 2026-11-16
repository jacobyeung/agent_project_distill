"""Explicit scalar renaming with a reversible proof of other JSON values."""
from copy import deepcopy
import hashlib
import re
BAD=re.compile(r'distill|qwen(?:35)?|vsi(?:590k)?|scannet|arkit|dev-?s1|native routed-read',re.I)

def neutral(value):
    return 'k'+hashlib.sha256(value.encode()).hexdigest()[:24]

def rename(value,mapping):
    if isinstance(value,str):return mapping.get(value,value)
    if isinstance(value,list):return [rename(v,mapping) for v in value]
    if isinstance(value,dict):
        result={rename(k,mapping):rename(v,mapping) for k,v in value.items()}
        if len(result)!=len(value):raise ValueError('Renaming collision')
        return result
    return value

def prove(original,renamed,mapping):
    if len(set(mapping.values()))!=len(mapping):raise ValueError('Ambiguous reverse mapping')
    inverse={v:k for k,v in mapping.items()}
    if rename(original,mapping)!=renamed or rename(renamed,inverse)!=original:
        raise ValueError('A value other than an approved name changed')
    return True

def scan_json(value,at='$'):
    hits=[]
    if isinstance(value,str):
        if BAD.search(value):hits.append(dict(location=at,value=value))
    elif isinstance(value,list):
        for i,v in enumerate(value):hits.extend(scan_json(v,at+'/'+str(i)))
    elif isinstance(value,dict):
        for k,v in value.items():
            if BAD.search(k):hits.append(dict(location=at+'/<key>',value=k))
            hits.extend(scan_json(v,at+'/'+k))
    return hits

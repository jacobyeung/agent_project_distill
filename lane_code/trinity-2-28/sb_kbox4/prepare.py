"""Extract train records from the two local mixed-split input containers.

The container bytes are hashed; held-out records are never JSON-decoded. This
is preparation, not permission to evaluate held-out data or write a split map.
"""
import hashlib
import json
from pathlib import Path
import re
from adapters import ROOT

MANIFEST=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
LABELS=Path('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl')


def main():
    data=MANIFEST.read_bytes()
    blocks=re.findall(r'^    \{\n.*?^    \}',data.decode(),re.M|re.S)
    if not blocks:raise ValueError('manifest_layout_changed')
    captures=[json.loads(b) for b in blocks if re.search(r'^      "k1_split": "train",?$',b,re.M)]
    assert captures and all(c['k1_split']=='train' for c in captures)
    pins={str(MANIFEST):hashlib.sha256(data).hexdigest()}
    (ROOT/'train_manifest.json').write_text(json.dumps(dict(input_sha256=pins,captures=captures))+'\n')
    ids={r['id'] for c in captures for r in c['rows']}
    data=LABELS.read_bytes();pins={**pins,str(LABELS):hashlib.sha256(data).hexdigest()}
    rows=[]
    for line in data.decode().splitlines():
        match=re.search(r'"id"\s*:\s*"([^"\\]+)"',line)
        if match and match[1] in ids:
            r=json.loads(line)
            if r['split']!='train':raise ValueError('label_split_conflict')
            rows.append(r)
    (ROOT/'train_labels.json').write_text(json.dumps(dict(input_sha256=pins,rows=rows))+'\n')
    (ROOT/'STATUS.md').write_text('Stage 1: Prepared existing train manifest records and corrected labels. Mixed-container bytes were hashed; held-out records were not decoded. No membership or labels were invented.\n')


if __name__=='__main__':main()

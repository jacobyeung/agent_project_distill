"""Summarize saved test reports and verify the cache-content witness and kit hashes."""
import json
from pathlib import Path
import torch
from eat1 import hook, run, scan
from eat1.artifact import Artifact, sha256
from probes_r2.variants import make_reader

ROOT = Path(__file__).resolve().parent
R = ROOT.parent


def main():
    original = {}
    for path in sorted((R/'tmp').glob('eat1_adv_*/runs/*/EAT1_REPORT.json')):
        data = json.loads(path.read_text())
        original[path.parent.name] = dict(report=str(path.relative_to(R)), overall=data['overall'],
            clauses={k: v['status'] for k, v in data['clauses'].items()},
            reasons={k: sorted({o.get('rule') or o.get('kind') or o.get('file', '')
                                for o in v['offenders']}) for k, v in data['clauses'].items()},
            a5_parts=data['clauses']['A5']['parts'])
    print('round1', json.dumps(original, sort_keys=True))
    reader = make_reader(ROOT/'fixture', 'permute')
    state, witnesses = {}, []

    def pre(module, args, kwargs):
        cache = kwargs.get('past_key_values')
        if cache is not None and 'last' in state:
            before, after = state['last'], cache.ids.data
            if not torch.equal(before, after):
                witnesses.append(dict(before=reader.tokenizer.decode(before.tolist()),
                                      after=reader.tokenizer.decode(after.tolist()),
                                      fingerprint_equal=hook._fingerprint(before) == hook._fingerprint(after)))

    def post(module, args, kwargs, output):
        state['last'] = output.past_key_values.ids.data.clone()

    reader.model.lm.register_forward_pre_hook(pre, with_kwargs=True)
    reader.model.lm.register_forward_hook(post, with_kwargs=True)
    records, _, _ = run.observe(reader, run.read_items(ROOT/'fixture/move.jsonl'),
                                Artifact(reader.artifact_manifest), trace_lines=False)
    print('cache_witness', json.dumps(dict(changed=bool(witnesses), witnesses=witnesses,
                                        violations=records[0]['provenance']['violations'])))
    allow = scan.load_allowlist(extra=[ROOT/'allow.json'])
    print('original_benign', json.dumps(scan.scan([R/'probes_r1/benign.py'], allow)[0]))
    bad = []
    for line in (R/'COPY_FILES.sha256').read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        if sha256(R/name) != digest:
            bad.append(name)
    print('original_hash_mismatches', json.dumps(bad))
    print('workspace_bytes', sum(p.stat().st_size for p in R.rglob('*') if p.is_file()))
    (ROOT/'round1_evidence.json').write_text(json.dumps(original, indent=2)+'\n')


if __name__ == '__main__':
    main()

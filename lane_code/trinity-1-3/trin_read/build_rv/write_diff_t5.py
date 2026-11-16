"""Write a line-complete source/output ledger against the read-only build sibling."""
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent/'build'
EXCLUDED = {'DIFF.md', 'DIFF_AUDIT_T5.json'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def classify(name, line):
    if name == 'trinity_read.py' and any(text in line for text in (
            "LLG_STUB =", "(AREA/'build', DEFAULT_ROOT)", '(BUILD, DEFAULT_ROOT)',
            'Writes must remain', 'trinity_runner', 'expected = LINEAGE',
            "parent = FSW/'ap/f2ad01ad", 'path in (parent, physical(root, parent))', 'expected = parent', 'EXPORT_RUNS', 'allowed = [FSW', 'allowed.append(parent)',
            'if type(step) is int', 'for expected in allowed', 'path in (expected, physical(root, expected))',
            'return str(expected)', 'allowed run and positive step')):
        return 'PATH/ENV'
    return 'BEYOND'


def main():
    paths = [p for p in HERE.iterdir() if p.is_file() and p.name not in EXCLUDED]
    paths += list((HERE/'tests').glob('*.py'))
    lines = ['# Changes relative to build/', '',
        'The baseline is the read-only sibling `../build/`. Every added or removed line in changed top-level files and test sources appears below, with old/new line numbers and a PATH/ENV or BEYOND classification. No Git command was used.', '',
        '`PATH/ENV` marks filesystem placement and lineage-path admission. `BEYOND` marks model/camera behavior, contracts, tests, documentation, and generated evidence.', '',
        '`DIFF.md` and its generated audit are excluded from their own ledger. Generated fixture trees (`fixture_*`, `validation/`, and `tests/t5_*`) contain copied kit sources and temporary bindings; they are not source edits and are represented by the final test log and BIND_PARITY_T5.json. All changed top-level evidence files are included.', '',
        'The accepted source, payload, export checker, and evaluator files outside build_t5 remain read-only. The runner uses a separate `trinity_runner_t5` bundle for production.', '']
    audit = {}
    for path in sorted(paths):
        name = str(path.relative_to(HERE)); before = BASE/name
        old = before.read_bytes() if before.exists() else b''
        new = path.read_bytes()
        if old == new: continue
        a,b=old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True)
        rows=[];counts={'removed':0,'added':0}
        for op,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
            if op == 'equal': continue
            for sign,seq,start,end,label in [('-',a,i,j,'removed'),('+',b,k,l,'added')]:
                for at in range(start,end):
                    line=seq[at];rows.append('[{}] {} {}:{} {}'.format(classify(name,line),sign,'old' if sign=='-' else 'new',at+1,json.dumps(line,ensure_ascii=False)))
                    counts[label]+=1
        audit[name]=dict(baseline_sha256=sha(old) if before.exists() else None,current_sha256=sha(new),**counts)
        lines += ['## '+name, '',
                  'Baseline SHA256: '+(sha(old) if before.exists() else 'absent')+'. Current SHA256: '+sha(new)+'.', '',
                  '`````text']+rows+['`````','']
    (HERE/'DIFF.md').write_text('\n'.join(lines)+'\n')
    (HERE/'DIFF_AUDIT_T5.json').write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(files=len(audit),added=sum(r['added'] for r in audit.values()),removed=sum(r['removed'] for r in audit.values()))))


if __name__ == '__main__':
    main()

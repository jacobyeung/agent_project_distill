#!/usr/bin/env python3
"""Package code only and assemble the report from verified output artifacts."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path
import re
import shlex
import tarfile

HERE=Path(__file__).absolute().parent
OUT=HERE/'out'
CODE=['callrate.py','return_reader.py','measurements.py','bootstrap.py','wording.py',
      'populations.py','reproduce.py','build_delivery.py','README.md','tests/test_callrate.py']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    reproduction=json.loads((OUT/'reproduction.json').read_text())
    if reproduction['status']!='PASS':
        raise ValueError('Reproduction did not pass')
    testlog=(OUT/'unit_tests.txt').read_text()
    match=re.search(r'Ran (\d+) tests in ([\d.]+)s\s+OK\s*$',testlog)
    if not match:
        raise ValueError('Unit tests did not pass')
    data={name:json.loads((OUT/name/'callrate.json').read_text()) for name in ['step200','room134']}
    # Check that reports correspond to the final code and unchanged input files.
    for s in reproduction['sources']:
        if digest(Path(s['path']))!=s['sha256']:
            raise ValueError('Input changed after reproduction: '+s['path'])
    archive=OUT/'sb_callrate.tar'
    with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as tar:
        for name in CODE:
            path=HERE/name
            info=tar.gettarinfo(str(path),arcname=name)
            info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0;info.mode=0o644
            with path.open('rb') as stream:
                tar.addfile(info,stream)
    archive_sha=digest(archive)
    (OUT/'sb_callrate.tar.sha256').write_text(archive_sha+'  sb_callrate.tar\n')
    with tarfile.open(archive) as tar:
        if sorted(tar.getnames())!=sorted(CODE):
            raise ValueError('Unexpected archive contents')
    sources={s['path']:s['sha256'] for s in reproduction['sources']}
    for name in CODE:
        sources[str(HERE/name)]=digest(HERE/name)
    for name in ['unit_tests.txt','reproduction_tests.txt','reproduction.json','step200/callrate.txt','room134/callrate.txt','step200/callrate.summary.txt','room134/callrate.summary.txt','sb_callrate.tar']:
        sources[str(OUT/name)]=digest(OUT/name)
    validation=dict(status='PASS',unit_tests=int(match[1]),reproduction_checks=len(reproduction['checks']),
                    archive_sha256=archive_sha,archive_members=CODE,
                    command=[sys.executable,'-B',str(Path(__file__).absolute())],
                    sources=[dict(path=p,sha256=s) for p,s in sorted(sources.items())])
    (OUT/'delivery_validation.json').write_text(json.dumps(validation,indent=2,allow_nan=False)+'\n')
    lines=['# Call-rate reader report','',
        f'The CLI passes {match[1]} synthetic, loader, and CLI tests and {len(reproduction["checks"])} reproduction checks. Camera and distance scores match `scoresAB/scores.json` bit for bit; their bootstrap outputs also match. Room134 reproduces 0 calls at step 200, 134 calls at step 544, and 115 capped items at step 544.','',
        'The archive contains code, the README, and tests only. No returns or data are included.',
        '',f'Archive: `sb_callrate.tar`  \nSHA-256: `{archive_sha}`','',
        '## Commands and validation','',
        'All commands ran on trinity-1-18 with CPU only, no network, and one BLAS/OpenMP thread. The commands below produce every reported metric. The synthetic step-400/600 CLI test verifies input hashes before and after execution.','',
        '```bash',
        'export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1',
        'python -B -m unittest discover -s tests -v > out/unit_tests.txt 2>&1',
        'python -B reproduce.py --input-root in --out out > out/reproduction_tests.txt 2>&1',
        'python -B build_delivery.py',
        '```','',
        'The reproduction command runs these two exact reader commands:', '','```bash']
    lines += [shlex.join(cmd) for cmd in reproduction['commands']]
    lines += ['```','',
        f'Unit tests: **{match[1]} passed** in {match[2]} s. Reproduction: **{len(reproduction["checks"])} checks passed**.',
        'Tests cover type-specific and unserved calls, cap reasons, unit conversion, response agreement/disagreement, absent responses, fixed direction math, room-area parsing, exact bootstrap equivalence, wording expressions, export steps, identity tampering, partial/duplicate journals, missing inputs, and read-only execution.',
        '', 'Logs: [unit tests](unit_tests.txt), [reproduction](reproduction_tests.txt), [per-check values](reproduction.json).',
        '', '## Reproduction table','',
        'A is step 200; B is registered step 544. Scores use the package scorer, and deltas use percentage points. Camera/distance values come from the first reader command; room134 values come from the second.', '',
        '| Population | n A/B | Calls A/B | Capped A/B | Score A | Score B | Score delta, 95% CI (pp) |',
        '|---|---:|---:|---:|---:|---:|---|']
    for run,kind,label in [('step200','camera_displacement','Camera displacement'),
                           ('step200','camera_rotation','Camera rotation'),
                           ('step200','camera_movement_direction','Camera direction'),
                           ('step200','object_abs_distance','Object distance'),
                           ('step200','room_size_estimation','Room36 (A4 subset)'),
                           ('room134','room_size_estimation','Room134 (B5)')]:
        row=data[run]['types'][kind];a,b=row['a'],row['b'];p=row['paired']['score']
        lines.append(f"| {label} | {a['n']}/{b['n']} | {a['call_count']}/{b['call_count']} | {a['capped_count']}/{b['capped_count']} | {a['score']:.9f} | {b['score']:.9f} | {p['value']:.6f} [{p['ci95'][0]:.6f}, {p['ci95'][1]:.6f}] |")
    lines += ['',
        'The two room rows overlap: the 36 A4 room IDs are part of room134. They are separate comparisons and must not be added. Default pairing uses b1/read 0 for camera types, b1/read 1 for distance, and b2/read 0 for rooms; it restricts B to A’s planned IDs.',
        '', '## Metric definitions and missing values','',
        '- Call rate counts recorded calls that belong to the item type, including unserved calls. Unrelated calls do not count.',
        '- Capped rate uses the exact `score_r5.py` definition: `max_calls`, `max_new_tokens`, or `length`. Its denominator includes all completed items, even when no call occurs.',
        '- Usage measures agreement with the last parsed matching response. It uses the scorer’s 5% relative tolerance (exact zero), requested units, direction argmax, and the room parser’s area. A called item with a parsed response but no final answer is an eligible failure.',
        '- Paired usage requires eligibility on both sides. Its delta can differ from the difference between marginal usage rates. Every paired metric uses the unchanged `score_r5.py` room bootstrap: seed 17, 10,000 draws, ratio estimator, and 95%/99.29% intervals.',
        '- Answer rate requires a final segment or explicit answer tag. The scorer suppresses answers when `finish=max_calls`.',
        '- Unit labels follow `scorers.unit_factor`; room labels denote square units, and non-length types use `N/A`. Distance wording reuses `classify.py` tags, which overlap. Other wording groups use questions with numbers and route object names masked.',
        '- Room usage is `MISSING` on both steps because neither supplies a parsed room response. Unknown types remain in the output; missing routing or response interpretation is explicitly `MISSING`, never an inferred mapping.',
        '', '## Step-200 versus step-544 output','',
        'The full JSON includes per-item measurements, all five paired metrics, 95%/99.29% intervals, coverage, input hashes, and symlink relocation records. Copied symlinks are resolved under `in/` without modifying them.',
        '', '[A4 JSON](step200/callrate.json) · [A4 table](step200/callrate.txt) · [Room134 JSON](room134/callrate.json) · [Room134 table](room134/callrate.txt)',
        '', 'A4 (636 items):', '', '```text', (OUT/'step200/callrate.txt').read_text().rstrip(), '```',
        '', 'Room134 (134 items):', '', '```text', (OUT/'room134/callrate.txt').read_text().rstrip(), '```',
        '', '[Delivery validation and source hashes](delivery_validation.json) authenticate the report inputs and archive.']
    lines += ['', '## Room populations and RESULT summary', '',
        'The authenticated B5 manifest resolves locally to `in/cont_ops/work/r1route/out3/B4/src/items/room134.json`. It and `bases/b2/src/items/room134.json` share SHA-256 `607ba5798f06b77e713069bc57a9ed3b0e80db78ef81faa945487fadddc5e9c7`. Their explicit `sets` identify 36 dev-S1 and 98 R0-dev items. No scene-list inference is needed.', '',
        'The second reproduction command above produces every value below. MRA answer averages all completed room items, including unanswered items. A is step 200 and B is registered step 544. The paired delta uses the unchanged seed-17, 10,000-draw physical-room bootstrap.', '',
        '| Population | n A/B | MRA A (%) | MRA B (%) | A−B (pp), 95% CI |',
        '|---|---:|---:|---:|---|']
    for population in ('dev-S1','R0-dev','all'):
        row=data['room134']['room_mra'][population];a,b,p=row['a'],row['b'],row['paired']
        lines.append(f"| {population} | {a['n']}/{b['n']} | {100*a['mra_answer']:.2f} | {100*b['mra_answer']:.2f} | {p['value']:.2f} [{p['ci95'][0]:.2f}, {p['ci95'][1]:.2f}] |")
    lines += ['',
        '`--summary` prints only the requested per-type metrics, distance call rates by unit, and room population MRA to stdout. Full output files remain available. The JSON records every input hash, population membership, counts, and both bootstrap intervals. Unknown membership says `MISSING` and exits 2.', '',
        'The first reproduction command above produces this one-screen RESULT:', '',
        '```text', (OUT/'step200/callrate.summary.txt').read_text().rstrip(), '```', '',
        'The README gives step-400 and step-600 commands. Tests exercise those steps with synthetic authenticated returns; measured step-400/600 results require the actual return paths.',
        'Tests also cover conflicting tags, unknown populations, exact catalog joins, incomplete population coverage, and shared-room bootstrap clustering. All original tests and reproduction checks remain enabled.']
    if len('\n'.join(lines).splitlines()) >= 200:
        raise ValueError('Report must remain under 200 lines')
    (OUT/'CALLRATE_REPORT.md').write_text('\n'.join(lines)+'\n')
    (HERE/'STATUS.md').write_text(f'Delivery is complete. The CLI supports --summary and room answer MRA by explicit dev-S1/R0-dev membership. It passes {match[1]} synthetic/loader/CLI tests and {len(reproduction["checks"])} reproduction checks, including all original checks, the five requested rounded MRA values, and exact population bootstrap outputs. out/CALLRATE_REPORT.md contains commands, results, and the appended population/summary section. out/sb_callrate.tar contains code, the README, and tests only; SHA-256 is {archive_sha}. Every output JSON records its input hashes. Step-400/600 CLI behavior is tested with synthetic returns; actual metrics require their return paths.\n')
    print(f'Archive SHA-256: {archive_sha}\nReport: {OUT/"CALLRATE_REPORT.md"}')


if __name__=='__main__':
    main()

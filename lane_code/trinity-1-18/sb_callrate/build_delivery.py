#!/usr/bin/env python3
"""Build a verified code archive and the call-rate report."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path
import re
import shlex
import tarfile

HERE = Path(__file__).absolute().parent
OUT = HERE/'out'
CODE = ['callrate.py','return_reader.py','measurements.py','bootstrap.py','wording.py',
        'populations.py','reproduce.py','review_probes.py','make_strata_example.py','build_delivery.py',
        'README.md','tests/test_callrate.py','tests/test_review_fixes.py','examples/devs1_wording_strata.json']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    reproduction = json.loads((OUT/'reproduction.json').read_text())
    probes = json.loads((OUT/'review_probes/review_probes.json').read_text())
    if reproduction['status'] != 'PASS' or probes['status'] != 'PASS':
        raise ValueError('Reproduction or review probes did not pass')
    testlog = (OUT/'unit_tests.txt').read_text()
    match = re.search(r'Ran (\d+) tests in ([\d.]+)s\s+OK\s*$',testlog)
    if not match:
        raise ValueError('Unit tests did not pass')
    sources = {}
    for evidence in (reproduction, probes):
        for source in evidence['sources']:
            if digest(Path(source['path'])) != source['sha256']:
                raise ValueError('Input changed after validation: '+source['path'])
            sources[source['path']] = source['sha256']
    data = {name:json.loads((OUT/name/'callrate.json').read_text()) for name in ('step200','room134','strata_example')}
    archive = OUT/'sb_callrate.tar'
    with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as tar:
        for name in CODE:
            path = HERE/name
            info = tar.gettarinfo(str(path),arcname=name)
            info.uid=info.gid=0; info.uname=info.gname=''; info.mtime=0; info.mode=0o644
            with path.open('rb') as stream:
                tar.addfile(info,stream)
    archive_sha = digest(archive)
    (OUT/'sb_callrate.tar.sha256').write_text(archive_sha+'  sb_callrate.tar\n')
    with tarfile.open(archive) as tar:
        if sorted(tar.getnames()) != sorted(CODE):
            raise ValueError('Unexpected archive contents')
    lines = ['# Call-rate reader report','',
        f'The reader passes {match[1]} unit tests, {len(reproduction["checks"])} reproduction checks, and {len(probes["checks"])} checks against the independent reviewer’s saved probes. All original reproduction checks remain enabled. Camera, distance and room36 primary scores and bootstrap intervals match `score_r5.py` outputs.', '',
        f'Archive: `sb_callrate.tar`  \nSHA-256: `{archive_sha}`', '',
        'The archive contains code, tests, documentation and the example strata mapping. It excludes returns and test fixtures.', '',
        '## Commands and validation', '',
        'These commands ran on trinity-1-18 with CPU only, no network and one BLAS/OpenMP thread. The reader commands recorded in the reproduction and review JSON files produce every metric below.', '',
        '```bash',
        'export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1',
        'python -B -m unittest discover -s tests -v > out/unit_tests.txt 2>&1',
        'python -B reproduce.py --input-root in --out out > out/reproduction_tests.txt 2>&1',
        'python -B review_probes.py --review-root /scratch/jjyeung/orch_n30/sb_crrev/scratch/rob --out out/review_probes > out/review_probes.txt 2>&1',
        'python -B build_delivery.py', '```', '',
        'The reproduction command invokes:', '', '```bash']
    lines += [shlex.join(cmd) for cmd in reproduction['commands']]
    lines += ['```', '',
        '[Unit-test log](unit_tests.txt) · [reproduction checks and hashes](reproduction.json) · [review probe checks and hashes](review_probes/review_probes.json)', '',
        '## Reproduction table', '',
        'A is step 200; B is registered step 544. Camera/distance and A4 room rows come from the first reader command; B5 room rows come from the second. Scores use package overrides when supplied. Deltas use percentage points.', '',
        '| Population / source reads A vs B | n/expected A / B | Calls A/B | Capped A/B | Score A | Score B | Score delta, 95% CI (pp) |',
        '|---|---:|---:|---:|---:|---:|---|']
    rows = [(data['step200']['types'][kind],label) for kind,label in
            [('camera_displacement','Camera displacement: A4/read 0 vs b1/read 0'),
             ('camera_rotation','Camera rotation: A4/read 0 vs b1/read 0'),
             ('camera_movement_direction','Camera direction: A4/read 0 vs b1/read 0'),
             ('object_abs_distance','Distance: A4/read 0 vs b1/read 1'),
             ('room_size_estimation','Room36 primary: A4/read 0 vs b1/read 0')]]
    rows += [(data['step200']['room_secondary'],'Room36 secondary: A4/read 0 vs b2/read 0'),
             (data['room134']['types']['room_size_estimation'],'Room134: B5/read 0 vs b2/read 0')]
    for row,label in rows:
        a,b,p = row['a'],row['b'],row['paired']['score']
        lines.append(f"| {label} | {a['n']}/{a['expected']} / {b['n']}/{b['expected']} | {a['call_count']}/{b['call_count']} | {a['capped_count']}/{b['capped_count']} | {a['score']:.9f} | {b['score']:.9f} | {p['value']:.6f} [{p['ci95'][0]:.6f}, {p['ci95'][1]:.6f}] |")
    lines += ['',
        'Room36 uses b1/read 0 because A4 is the registered five-type read. The b2/read 0 comparison is secondary. The room36 and room134 populations overlap and must not be added.', '',
        '## Metric definitions and missing values', '',
        '- Call rate counts recorded calls of the item type, including unserved calls. Capped rate counts `max_calls`, `max_new_tokens` and `length` over all compared items.',
        '- Usage means the answer follows the response: `follow_converted + copied_unconverted`. Category rates divide by items with parsed responses; a missing answer is `other`. Converted agreement takes precedence at zero, where copying and conversion cannot be distinguished.',
        '- `conversion_failure` counts unconverted copies among response-eligible questions requiring a unit conversion. Room area uses squared units; camera displacement uses length units.',
        '- Answer rate counts finite values parsed by the type scorer or listed options. `not_seen` and `other_non_numeric` have separate rates over compared items. `max_calls` suppresses answers.',
        '- Scores preserve package accuracy and supplied `scores.answer` overrides. Numeric-task scores are MRA. MRA includes unanswered/capped items and is not answer rate.',
        '- Marginals and deltas use shared completed IDs. Paired usage additionally requires response eligibility on both sides. Intervals retain the seed-17, 10,000-draw physical-room bootstrap.',
        '- Missing responses make usage `MISSING`; room usage is MISSING in these reads. Population membership uses explicit manifest tags or identity-checked joins. Unknown membership is never guessed.', '',
        '## Room populations and RESULT summary', '',
        'The second reader command yields these room MRAs. The explicit manifest contains 36 dev-S1 and 98 R0-dev items. The A4 dev-S1 population is separately labelled in the primary table and summary.', '',
        '| Population / source reads A vs B | n/expected A / B | MRA A (%) | MRA B (%) | Delta, 95% CI (pp) |',
        '|---|---:|---:|---:|---|']
    for label in ('dev-S1','R0-dev','all'):
        row = data['room134']['room_mra'][label]; a,b,p = row['a'],row['b'],row['paired']
        lines.append(f"| {label}: B5/read 0 vs b2/read 0 | {a['n']}/{a['expected']} / {b['n']}/{b['expected']} | {100*a['mra_answer']:.2f} | {100*b['mra_answer']:.2f} | {p['value']:.2f} [{p['ci95'][0]:.2f}, {p['ci95'][1]:.2f}] |")
    lines += ['', '[A4 table](step200/callrate.txt) · [A4 summary](step200/callrate.summary.txt) · [A4 JSON](step200/callrate.json) · [Room134 table](room134/callrate.txt) · [Room134 JSON](room134/callrate.json)', '',
        '## Review fixes', '',
        'The review-probe command above reruns the supplied t2/t3/t4 cases with outputs confined to this workspace. The review fixtures remain read-only.', '',
        '- **Partial summaries:** t2 refuses with exit 2, empty stdout and one stderr line. With `--allow-partial --allow-subset`, it prints PARTIAL, distance 100/150 and room 20/36, and computes both sides on those shared IDs.',
        '- **Mismatched populations:** t4 refuses without `--allow-subset`. With it, the room row prints original planned sizes A=36, B=134 and compares only the 36 shared IDs; both marginals use that set.',
        '- **Symlink relocation:** t3 reproduces the reference metrics with the default original root. Existing targets are retained even when a stale relocated target exists. Only missing targets under the original root relocate.',
        '- **Authentication and resumes:** wrong steps, bindings, packages, duplicate rows, uncommitted tails and started segments without journals still refuse. The legitimate two-segment resume matches the complete read.',
        '- **Test isolation:** fixtures use temporary directories under `scratch/tests`; path assertions derive from temporary paths or stable suffixes.', '',
        'The first reproduction reader command produces the response-following and answer results below:', '',
        '| Distance metric | A4/read 0 (step 200) | b1/read 1 (step 544) |',
        '|---|---:|---:|']
    distance = data['step200']['types']['object_abs_distance']
    for key,label in [('usage','Usage'),('follow_converted','Follow converted'),('copied_unconverted','Copied unconverted'),('other','Other'),('conversion_failure','Conversion failure'),('answer','Parseable answer'),('not_seen','Not seen'),('other_non_numeric','Other non-numeric')]:
        values=[]
        for side in ('a','b'):
            v=distance[side]
            denominator = v[key+'_n']
            values.append(f"{v[key+'_count']}/{denominator} ({100*v[key+'_count']/denominator:.2f}%)")
        lines.append('| '+label+' | '+' | '.join(values)+' |')
    groups = data['strata_example']['types']['object_abs_distance']['by_stratum']
    lines += ['',
        'Room36 primary reproduces B=0.116667, capped 29/36, and delta 55.28 [38.82, 70.39]. Its labelled secondary b2/read 0 comparison gives delta 55.83 [39.50, 70.50].', '',
        f'**External strata:** `--strata FILE` adds per-stratum and per-stratum-by-unit call rates and score/MRA to the table and summary. The example generator command freezes the existing dev-S1 A4 trace tags for 150 distance IDs into {len(groups)} labels. The reproduction checks confirm that these rows partition the same items and leave per-item measurements unchanged.', '',
        'The example labels describe generated traces, not question-wording effects or HELDOUT/TRAIN_DEV/R0_REWORDED membership. No dist_diag split is inferred. Supply its explicit ID mapping when available. Units must match questions, and missing labels within a represented type say MISSING and exit 2.', '',
        '[Example mapping](../examples/devs1_wording_strata.json) · [stratified table](strata_example/callrate.txt) · [stratified summary](strata_example/callrate.summary.txt)', '',
        'The README documents the schema, denominators, opt-in flags and step-400/600 commands. Real step-400/600 metrics require those returns; synthetic tests cover their CLI behavior.', '',
        '[Delivery validation](delivery_validation.json) records input hashes, archive contents, checks and this report’s hash.']
    report = '\n'.join(lines)+'\n'
    if len(report.splitlines()) >= 250:
        raise ValueError('Report must remain under 250 lines')
    (OUT/'CALLRATE_REPORT.md').write_text(report)
    for name in CODE:
        sources[str(HERE/name)] = digest(HERE/name)
    for name in ('unit_tests.txt','reproduction_tests.txt','reproduction.json','review_probes.txt','review_probes/review_probes.json',
                 'step200/callrate.txt','room134/callrate.txt','step200/callrate.summary.txt','room134/callrate.summary.txt',
                 'strata_example/callrate.txt','strata_example/callrate.summary.txt','sb_callrate.tar','CALLRATE_REPORT.md'):
        sources[str(OUT/name)] = digest(OUT/name)
    validation = dict(status='PASS',unit_tests=int(match[1]),reproduction_checks=len(reproduction['checks']),
        review_probe_checks=len(probes['checks']),archive_sha256=archive_sha,archive_members=CODE,report_lines=len(report.splitlines()),
        command=[sys.executable,'-B',str(Path(__file__).absolute())],
        sources=[dict(path=p,sha256=s) for p,s in sorted(sources.items())])
    (OUT/'delivery_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    (HERE/'STATUS.md').write_text(f'Review fixes are complete. The reader passes {match[1]} unit tests, {len(reproduction["checks"])} reproduction checks and {len(probes["checks"])} independent-review probe checks. Summary coverage, shared-ID pairing, conversion categories, parseable answers, registered room36 pairing, safe relocation and external strata are validated. out/CALLRATE_REPORT.md records commands and results in {len(report.splitlines())} lines. out/sb_callrate.tar includes the reader, tests, documentation and the provenance-backed example strata file; SHA-256 is {archive_sha}.\n')
    print(f'Archive SHA-256: {archive_sha}\nReport: {OUT/"CALLRATE_REPORT.md"} ({len(report.splitlines())} lines)')


if __name__ == '__main__':
    main()

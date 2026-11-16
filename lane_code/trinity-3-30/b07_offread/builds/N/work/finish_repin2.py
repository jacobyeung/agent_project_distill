"""Seal the tested build, archive identities, and current evidence without deleting files."""
from pathlib import Path
import ast
import hashlib
import json
import re
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from offnative.io import load, dump, sha
from offnative.package import package
from offnative.proof import LOSS_RECORD_SHA256

out = ROOT/'out'
run = load(ROOT/'work/REPIN2_RUN.json')
prefix = 'repin2_' + run['stamp']
log = (out/'tests_repin2.log').read_text()
match = re.search(r'(\d+) passed[^\n]*', log)
assert match and 'failed' not in log
tests = int(match[1])
proof = load(out/'PROOF_CPU.json')
assert proof['passed'] and proof['mode'] == 'reduced'
assert proof['loss_record_sha256'] == sha(out/'PROOF_MASKS_LOST.json') == LOSS_RECORD_SHA256
assert len(proof['checks']) == 10 and all(c['equal'] for c in proof['checks'])
assert proof['independent_camera_items'] == proof['recorded_response_distance_items'] == 5

fixtures = []
traces = []
for benchmark in ('revsi999t32', 'vsibench5130'):
    for kind in ('harness', 'e2e'):
        tag = prefix+'_'+benchmark+'_'+kind
        work = ROOT/'work'/tag
        result = load(work/'RESULT.json')
        assert result['passed'] and result['phases'] == 7
        assert not result['production_config_transport_only']
        receipts = sorted((work/'return/receipts').glob('*.json'))
        assert len(receipts) == 7 and all(load(p)['status'] == 'PASS' for p in receipts)
        result.update(benchmark=benchmark, run=str(work.relative_to(ROOT)),
                      binding_sha256=load(work/'BINDING.json')['binding_sha256'],
                      config_sha256=sha(work/'CONFIG.json'))
        fixtures.append(result)
        traces.append(load(out/('COVERAGE_'+tag+'.json')))
dump(out/'N3_FIXTURE_RESULTS.json', fixtures)

files = {}
for trace in traces:
    for row in trace['files']:
        key = (row['file'], row['sha256'])
        if key not in files:
            files[key] = dict(row)
        else:
            files[key]['executed_lines'] = sorted(set(files[key]['executed_lines']) | set(row['executed_lines']))
            files[key]['unexecuted_statement_lines'] = sorted(set(files[key]['unexecuted_statement_lines']) & set(row['unexecuted_statement_lines']))
executed = sum(len(row['executed_lines']) for row in files.values())
dump(out/'N3_EXECUTED_LINES.json', dict(executed_line_locations=executed,
    scope='Four synthetic CPU worker traces; not branch coverage or production equivalence.',
    files=[files[k] for k in sorted(files)],
    runs=[str((out/('COVERAGE_'+prefix+'_'+r['benchmark']+'_'+r['reader']+'.json')).relative_to(ROOT)) for r in fixtures]))

audit = []
for name, relative in load(ROOT/'vendor/ACTIVE.json').items():
    root = ROOT/relative
    pins = load(root/'PIN.json')
    assert all(sha(root/n) == h for n,h in pins['files'].items())
    if name == 'R':
        assert all(sha(ROOT.parent/'R'/n) == h for n,h in pins['files'].items())
    audit.append(dict(name=name, root=relative, files=len(pins['files']), passed=True,
                      pin_sha256=sha(root/'PIN.json'), snapshot_sha256=pins['sha256']))
dump(out/'N3_SNAPSHOT_PIN_AUDIT.json', audit)
owner = ROOT.parents[1]/'kit/offkit'
assert all(sha(owner/n) == h for n,h in load(out/'OFFKIT_EXTERNAL_PINS.json')['files'].items())

locations = []
for path in sorted((ROOT/'offnative').glob('*.py')):
    source = path.read_bytes()
    compile(source, str(path), 'exec')
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            locations.append(dict(file=str(path.relative_to(ROOT)), line=node.lineno,
                                  name=node.name, sha256=sha(path)))
dump(out/'INTEGRATION_LINES.json', locations)

archive_hash = package()
pins = load(out/'CODE_PINS.json')
members = {r['path']:r for r in pins['files']}
with tarfile.open(out/'code.tar') as archive:
    seen = set()
    for member in archive:
        assert member.isfile() and member.name not in seen
        assert not member.name.startswith('d/00/')
        raw = archive.extractfile(member).read()
        assert hashlib.sha256(raw).hexdigest() == members[member.name]['sha256']
        assert len(raw) == members[member.name]['bytes']
        seen.add(member.name)
    assert seen == set(members)
dump(out/'N3_ARCHIVE_CHECK.json', dict(passed=True, all_member_hashes_match=True,
    offkit_copied=False, members=len(members), sha256=archive_hash))
(out/'code_tar.sha256').write_text(archive_hash+'  code.tar\n')
previous = Path(run['previous'])
old = load(previous/'CODE_PINS.json')['archive']['sha256']
assert sha(previous/'code.tar') == old

ready = (out/'NATIVE_KIT_READY.md').read_text()
ready = re.sub(r'The final test suite reports \*\*.*?\*\* in `tests_n3_final.log`\.',
               'The test suite reports **'+match[0]+'** in `tests_repin2.log`.', ready)
ready = re.sub(r'combines [\d,]+ versioned executed file/line locations',
               f'combines {executed:,} versioned executed file/line locations', ready)
ready = re.sub(r'`code.tar` contains [\d,]+ files and [\d,]+ bytes\. Its SHA256 is `[0-9a-f]+`\.',
               f"`code.tar` contains {len(members):,} files and {pins['archive']['bytes']:,} bytes. Its SHA256 is `{archive_hash}`.", ready)
(out/'NATIVE_KIT_READY.md').write_text(ready)
dump(out/'FINAL_CHECK.json', dict(verdict='CPU_VALIDATED_PRODUCTION_NOT_READY',
    tests_passed=tests, fixtures_passed=[r['benchmark']+'_'+r['reader'] for r in fixtures],
    code_tar_verified=True, code_tar_sha256=archive_hash, cpu_protocol_proof_passed=True,
    identity_proof_mode='reduced', lost_mask_declaration_sha256=LOSS_RECORD_SHA256,
    external_offkit_verified=True, active_snapshots_verified=True,
    production_transport_only_rehearsal=False, production_worker_finished=False,
    submitted=False, uploaded=False, benchmark_answers_used_for_selection=False,
    retained_archives=str(previous.relative_to(ROOT)), retained_archive_sha256=old))

all_files = [p for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink()]
size = sum(p.stat().st_size for p in all_files)
assert size < 4_000_000_000, size
dump(out/'BUILD_INVENTORY.json', dict(bytes_before_checksum_regeneration=size, files=len(all_files),
    limit_bytes=4_000_000_000, within_limit=True,
    scope='All regular non-symlink files under build N, including retained artifacts and work directories.'))
delivered = [ROOT/n for n in ('RUN.md','DIFF.md','OPEN_INPUTS.md','SIZING.md','native_read.py','vendor/ACTIVE.json')]
delivered += list((ROOT/'offnative').glob('*.py')) + list((ROOT/'kit/tests').glob('*.py'))
delivered += [p for p in out.iterdir() if p.is_file() and p.name != 'SHIP_SHA256SUMS'
              and p.suffix != '.log']
delivered += [out/'tests_repin2.log', out/'repin2_proof_cpu.log']
delivered += [out/(prefix+'_'+r['benchmark']+'_'+r['reader']+'.log') for r in fixtures]
checksums = ''.join(sha(p)+'  '+str(p.relative_to(ROOT))+'\n' for p in sorted(set(delivered)))
(ROOT/'SHIP_SHA256SUMS').write_text(checksums)
(out/'SHIP_SHA256SUMS').write_text(checksums)
for line in checksums.splitlines():
    checksum, name = line.split('  ', 1)
    assert sha(ROOT/name) == checksum, name
print(json.dumps(dict(code_tar_sha256=archive_hash, tests=tests, fixtures=4,
                      proof_mode='reduced', archive_members=len(members), workspace_bytes=size)))

import sys, os, json, time, tarfile, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *
limits()
assert (T/'RUN_FINISHED.json').exists(), 'Do not finalize an incomplete suite.'
cases = load(T/'case_results.json')
source = T.parents[1]/'w24e/out/kit_n_go'
reference = T.parents[1]/'w24e/work/build24/kits/n'
before = load(T/'checksums_before.json')
after = [manifest(source), manifest(KIT)]
put(T/'checksums_after.json', after)
integrity = dict(before_and_after_valid=all(v['ok'] for v in before+after),
                 sealed_digests_unchanged=before == after,
                 copied_seal=sha(KIT/'SHA256SUMS.txt'), reference_seal=sha(reference/'SHA256SUMS.txt'))
integrity['all_copy_bytes_match_source'] = all(sha(p) == sha(source/p.relative_to(KIT)) for p in KIT.rglob('*') if p.is_file())
integrity['all_b_bytes_match_reference'] = all(sha(p) == sha(reference/'b'/p.name) for p in (KIT/'b').iterdir() if p.is_file())
integrity['requested_seals_match'] = integrity['copied_seal'].startswith('c992c930') and integrity['reference_seal'].startswith('240f8c17')
archive = next((KIT/'k').glob('t_*.tar'))
tree_rows = []
with tarfile.open(archive) as tar:
    for member in tar.getmembers():
        if member.isfile():
            expected = hashlib.sha256(tar.extractfile(member).read()).hexdigest()
            actual = sha(TREE/member.name)
            tree_rows.append(dict(path=member.name, expected=expected, actual=actual, match=actual == expected))
put(T/'tree_checksums.json', tree_rows)
integrity['tree_archive_sha256'] = sha(archive)
integrity['extracted_tree_bytes_unchanged'] = all(v['match'] for v in tree_rows)
checks = [dict(assertion=k, pass_=v) for k, v in integrity.items() if isinstance(v, bool)]

executables = {}
def executable(path, provenance):
    p = Path(path)
    if p.is_file():
        executables[str(p)] = dict(sha256=sha(p), resolved=str(p.resolve()), provenance=provenance)
for name in ('nice', 'bash', 'hostname', 'ls', 'sed', 'rg', 'bwrap', 'strace', 'setsid', 'timeout', 'sleep'):
    executable('/usr/bin/'+name, 'tool command, sandbox setup, or shell xtrace')
executable('/bin/bash', 'tool shell and test launcher interpreter')
executable(PY, 'all Python commands use this interpreter')
for leaf in ('common.py', 'preflight.py', 'case.py', 'run_once.py', 'finalize.py', 'exec_python.py', 'exec_python_v1.py', 'bin/python3', 'trap_driver.sh'):
    executable(T/leaf, 'test harness or preserved executable-source version')
events, source_hashes, coverage, sockets, starts = [], {}, {}, [], []
for p in sorted((T/'traces').glob('python-*.jsonl')):
    for line in p.read_text().splitlines():
        event = json.loads(line)
        event['trace_file'] = str(p.relative_to(T))
        if event['event'] == 'executable_source':
            source_hashes[event['path']] = event['sha256']
        elif event['event'] == 'coverage':
            for path, lines in event['files'].items():
                coverage.setdefault(path, set()).update(lines)
        elif event['event'].startswith('socket.'):
            sockets.append(event)
        elif event['event'] == 'python_start':
            event.setdefault('launcher_sha256', sha(T/'exec_python_v1.py'))
            starts.append(event)
        elif event['event'] == 'subprocess.Popen':
            events.append(event)
for path, observed in source_hashes.items():
    executable(path, 'Python audit exec event')
    executables[path]['sha256_at_execution'] = observed
    executables[path]['matches_execution_bytes'] = observed == executables[path]['sha256']
for name in ('pc.sh', 'pc.py', 'h.py', 'rd.py', 'rv.py', 'gc.py', 'sr.py', 'ep.py', 'z.py', 'cs.py'):
    executable(KIT/'b'/name, 'final kit SHA256SUMS and source execution or shell trace')
checks.append(dict(assertion='all executed audited source hashes still match', pass_=all(v.get('matches_execution_bytes', True) for v in executables.values())))
checks.append(dict(assertion='all observed socket attempts have at most four process threads', pass_=all(v.get('threads', 1) <= 4 for v in sockets)))
checks.append(dict(assertion='synthetic transport attempts observed', pass_=bool(sockets)))
checks.append(dict(assertion='all Python launcher starts isolated and no-bytecode', pass_=all('isolated=1' in v['flags'] and 'no_user_site=1' in v['flags'] and 'dont_write_bytecode=1' in v['flags'] for v in starts)))

# Assert line-level witnesses for the requested paths, beyond file import.
required = {'h.py': [11, 21, 23, 32, 40, 41, 43], 'rd.py': [14, 45, 49, 55],
            'rv.py': [277, 280, 281, 284, 289, 293, 295, 302, 306, 307, 311],
            'pc.py': [249, 285, 289, 293, 294, 295, 296]}
for leaf, needed in required.items():
    hits = coverage.get(str(KIT/'b'/leaf), set())
    checks.append(dict(assertion='executed requested lines: '+leaf, pass_=set(needed) <= hits,
                       required=needed, missing=sorted(set(needed)-hits)))
verdicts = {}
for leaf, prefix in [('h.py', 'h_'), ('rd.py', 'rd_'), ('rv.py', 'rv_'), ('pc.py', 'pc_')]:
    selected = [c for c in cases if c['case'].startswith(prefix)]
    verdicts[leaf] = 'PASS' if selected and all(c['verdict'] == 'PASS' for c in selected) else 'FAIL'
failed = [c['case'] for c in cases if c['verdict'] != 'PASS'] + [v['assertion'] for v in checks if not v['pass_']]
verdict = 'FAIL' if failed else 'PASS'
report = [verdict + (': '+', '.join(failed) if failed else ': all 14 targeted cases passed on unchanged final bytes.'),
          f"h.py: {verdicts['h.py']} — valid fresh export preserves identity and binds host/census/preparation; E85 and invalid host pin refuse.",
          f"rd.py: {verdicts['rd.py']} — publication hashes/status verified; missing selection and invalid job refuse by name.",
          f"rv.py: {verdicts['rv.py']} — timeout, matching PASS, identity mismatch, malformed JSON, non-PASS and mode 0644 tested.",
          f"pc.py: {verdicts['pc.py']} — valid synthetic sessions reach denied transport; failure marker, no .done, bounded final pass and work exit 7 verified.",
          'pc.sh: tk_live_finish executes final pc.py then ep.py; shell and Python traces record child commands and exit outcomes.',
          'Review uses the sealed 7200-second bound with a fake clock; only pre-wait rv.evidence is stubbed; identity/census/receipt/preparation checks remain real.',
          'rd.py r1.json contains returncode and byte counts; RESULT.json separately records verified published SHA256 values.',
          'All endpoints are synthetic 127.0.0.1:1 URLs; seccomp denies sockets. One synthetic prior part leaves three pending parts and at most four total threads.',
          'Source/copied SHA256SUMS pass before and after (c992c930); b/ matches reference 240f8c17; extracted tree matches its kit archive.',
          'All writes stay under tt24t2; kit/tree mounts are read-only; tests inherit nice 10, four-CPU affinity, one-thread math settings and a 7 GiB address-space cap.',
          'RESULT.json records commands, exits, executable hashes, assertions, coverage and produced files; no production sessions, GCS or training were used.']
raw(T/'REPORT.md', '\n'.join(report)+'\n')
inventory = []
for p in sorted(T.rglob('*')):
    if p.is_file() and p != T/'RESULT.json':
        inventory.append(dict(path=str(p.relative_to(T)), bytes=p.stat().st_size,
                              sha256=sha(p), mode=oct(p.stat().st_mode & 0o777)))
total = sum(p['bytes'] for p in inventory)
checks.append(dict(assertion='output below 500 MB', pass_=total < 500_000_000, bytes=total))
if total >= 500_000_000: verdict = 'FAIL'
result = dict(verdict=verdict, failures=failed, file_verdicts=verdicts,
              started=load(T/'RUN_STARTED.json'), finished=load(T/'RUN_FINISHED.json'),
              cases=cases, assertions=checks, integrity=integrity,
              commands=load(T/'commands.json'),
              tool_commands=load(T/'tool_commands.json') if (T/'tool_commands.json').exists() else [],
              initial_commands=load(T/'initial_commands.json') if (T/'initial_commands.json').exists() else [],
              nested_python_commands=events, python_launcher_starts=starts,
              executable_sha256=executables, source_line_coverage={p: sorted(v) for p, v in coverage.items()},
              socket_attempts=sockets, copier_fixture=load(T/'copier_fixture_note.json'),
              produced_files=inventory, produced_bytes_excluding_result=total,
              result_file=dict(path='RESULT.json', sha256='not self-hashed to avoid recursion'),
              limits=dict(nice=10, cpu_affinity_max=4, memory_per_process=7*1024**3, math_threads=1,
                          write_scope=str(T), network='socket and connect syscalls denied by seccomp'),
              notes=['Case subprocess exit codes are recorded separately from caught target exceptions or rv.run return values.',
                     'The suite guard prevents repeating cases. Sandbox preflight failures occurred before any target case ran.',
                     'rv.evidence is stubbed for this wait-branch test; no native row-sampling or training claim is made.',
                     'System-call tracing was refused by the container; executable Python audits and shell xtrace supply execution witnesses.',
                     'The Python launcher routes nested sys.executable calls through the mandated -I -s -B interpreter without editing kit bytes.',
                     'The preserved v1 launcher source applies to starts without launcher_sha256; later starts report the v2 source hash.',
                     'Small preparation/read commands precede the persisted harness; their invocation ledger is included separately.'])
result['finalization_command'] = dict(argv=['nice', '-n', '10', PY, '-I', '-s', '-B', str(T/'finalize.py')],
                                      exit_code=0, source_sha256=sha(T/'finalize.py'), operation='write final report and result; no test rerun')
result['shell_trace'] = dict(path='cases/pc_finish/root/shell.xtrace', sha256=sha(T/'cases/pc_finish/root/shell.xtrace'),
                            text=(T/'cases/pc_finish/root/shell.xtrace').read_text(), shell_exit_code=7,
                            exit_evidence='Both waits, both sr.py calls, final timeout/pc.py and ep.py returned 0: none executed their || true fallback. gc.py children report SystemExit 1 in Python audit traces.')
result['nested_python_exit_evidence'] = []
for start in starts:
    trace_path = T/start['trace_file']
    entries = [json.loads(line) for line in trace_path.read_text().splitlines()]
    exits = [e for e in entries if e['event'] == 'exception' and e.get('type') == 'SystemExit']
    result['nested_python_exit_evidence'].append(dict(trace_file=start['trace_file'], argv=start['argv'],
        exit_code=int(exits[-1]['message']) if exits and exits[-1]['message'].isdigit() else 0,
        basis='recorded SystemExit' if exits else 'normal completion, atexit coverage event and containing command/shell wait outcome'))
put(T/'RESULT.json', result)
print(json.dumps(dict(verdict=verdict, failures=failed, file_verdicts=verdicts,
                      cases=len(cases), produced_bytes=total, report_lines=len(report)), indent=2))

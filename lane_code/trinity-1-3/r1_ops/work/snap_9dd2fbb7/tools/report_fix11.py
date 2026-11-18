"""Record packet A's proof environment, validation and snapshot diff."""
import difflib
import json
import re
from pathlib import Path
from rebind import ROOT, load, sha, write

SNAP = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052')


def main():
    out = ROOT/'out'
    binding = load(out/'BINDING.json')
    op = load(out/'OPERATOR.json')
    assert (out/'config.json').read_bytes() == (SNAP/'out/config.json').read_bytes()
    assert (ROOT/'configs/r1p.json').read_bytes() == (SNAP/'configs/r1p.json').read_bytes()
    assert (out/'BINDING.json').read_bytes() == (SNAP/'out/BINDING.json').read_bytes()
    assert sha(out/op['archive']) == op['sha256']
    for name, expected in load(out/'FIX11_PROTECTED_ARCHIVES.json').items():
        assert sha(ROOT/name) == expected, name
    shell = (out/'logs/fix11_shell_tests.log').read_text()
    assert shell.rstrip().endswith('OK')
    focused_count = int(re.search(r'Ran (\d+) tests', shell).group(1))
    tests = (out/'logs/tests.log').read_text()
    checks = out/'logs/fix11_local_checks.log'
    passed = (checks.exists() and '"status": "BUILT_BLOCKED"' in checks.read_text()
              and 'Fix11.' in tests and tests.rstrip().endswith('OK'))
    count = int(re.search(r'Ran (\d+) tests', tests).group(1)) if passed else None
    status = 'BUILT_FOR_REVIEW' if passed else 'BUILT_PENDING_FULL_LOCAL_CHECKS'
    write(out/'FIX11_RESULT.json', dict(status=status, config_identity=binding['config_identity'],
        config_fields_changed=[], run_key=binding['run_key'], archive=op['archive'], sha256=op['sha256'],
        focused_tests=focused_count, all_tests=count, run_local_checks='PASS' if passed else 'NOT_RUN_PENDING_HEAVY_IO_APPROVAL',
        fixed=['TK_JOBDIR', 'R1_RUNTIME_RECORD'], caller_parity=['TK_RUNS_DIR'],
        snapshot=str(SNAP), production_authorized=False))
    validation = (f'All {count} tests pass through `tools/run_local_checks.py`; the seven focused regressions also pass separately. '
        'The check runner verifies two identical archives, two equal kit derivations, four-rank D0 optimizer identity, '
        'the CPU first-batch fixture, native selection regeneration, deployment evidence guards and every packet test.'
        if passed else f'All {focused_count} focused regressions pass. The full suite and `tools/run_local_checks.py` '
        'await explicit heavy-I/O approval under the supplied Trinity rule; they have not been run for this fix.')
    text = f'''{status}. Packet A has S2 on. The proof initializes its own shell environment before the loader audit.

Config identity: `{binding['config_identity']}` (unchanged; zero config-field changes).
Run key: `{binding['run_key']}`. Archive: `{op['archive']}`.
Archive SHA256: `{op['sha256']}`.

The generated `out/proof/p.py` embeds the post-admission shell in `program()`. `tools/make_proof.py` compresses this program into `p_{binding['run_key']}.sh`; `tools/package_operator.py` includes that script in the archive. The bundle's `p.py` is the unchanged `tools/seal_proof.py`, which binds the script bytes in the authority's `bundle_files`.

The proof runs `r.sh p 0` in a child shell, then sources `c.sh` in its caller. Child exports cannot initialize the caller. The caller explicitly exports `TK_JOBDIR` and reconstructs `R1_RUNTIME_RECORD` from the pinned staged record. It also exports `TK_RUNS_DIR=$NR` for consistency with the training entry.

`TK_JOBDIR` is `/tmp/jjyeung/a_{binding['run_key']}/jobs/${{SLURM_JOB_ID}}.proof` inside the proof namespace. The existing `/tmp` bind maps it to `/tmp/jjyeung/p_{binding['run_key']}_${{SLURM_JOB_ID}}/tmp/jjyeung/a_{binding['run_key']}/jobs/${{SLURM_JOB_ID}}.proof` on the host. The proof sets umask 077 and creates the leaf with `mkdir -m 700` before `tk_bwrap`. A pre-existing directory or symlink fails. No writable mount is added.

`tk_current record` supplies the runtime-record SHA. The caller verifies `$S/c7d31ddd/anyhost/<sha>.json` with `sha_is` and exports its namespace path `$P/anyhost/<sha>.json`. `tk_env` then exports the same path as `ANYHOST_NEUTRAL_RUNTIME`. The staged bytes remain read-only; caches and temporary files use the private proof job directory.

| Shell dependency | Source and use |
|---|---|
| `TK_KIT_HOME`, `ROOT` | The proof sets `TK_KIT_HOME=$ROOT` before sourcing; `ROOT` is the validated kit path from the generated job prefix. |
| `SLURM_JOB_ID` | Proof `main()` requires a positive numeric allocation ID; shell expansion uses `${{SLURM_JOB_ID:?}}`. |
| `TK_JOBDIR` | The proof creates a fresh 0700 `.proof` directory before `tk_bwrap` or `tk_env`. |
| `R1_RUNTIME_RECORD` | The proof resolves and verifies the record already staged by admission. It does not depend on a child export. |
| `TK_RUNS_DIR` | The proof exports `$NR`; `r.sh` obtains the same run parent from the pinned launch record. No current `c.sh` expansion requires this variable. |
| `AS AL K X R HX IN REV P RR EPOCHS S U HM NX NR CUR COMMIT CLOSURE_DIR` | Sourcing the sealed `c.sh` initializes all of them before functions run. `COMMIT` and `CLOSURE_DIR` come from pinned `k/0.json`. |
| `BW` | `tk_bwrap` initializes the array before the loader command expands it. Its `bw`, `sha` and `entry` locals are assigned by `read` and iteration. |
| `ANYHOST_JOBS PILOT_VENV PYTHONPATH TMPDIR` | `tk_env` initializes these before `tk_pythonpath p` and the loader call. All other runtime exports are constants or derived from the initialized paths. |
| `TK_LIGHT` | Staging reads it only through `${{TK_LIGHT:-}}`; `r.sh` explicitly sets or unsets it for its own stage. |
| `TK_JOB_START`, `TK_STAGE_ROOT` | The wrapper/job prefix sets `TK_JOB_START`; preflight exports `TK_STAGE_ROOT=$S` in its child. Neither is read by the post-admission `c.sh` functions or the loader-audit entry. |

The audit covers all 28 uppercase shell-variable reads in the entire staged `c.sh`, including staging and persistence. `ENVIRONMENT_AUDIT11.json` assigns each read an owner. Function parameters use guarded arguments or are supplied by their caller; staging locals receive their values before use from assignments, `read`, or loop bindings. `r.sh` and `p0.sh` already initialize `TK_JOBDIR` before their staging calls. `tk_stage` initializes `R1_RUNTIME_RECORD` before their `tk_env` calls. The proof does not repeat staging after admission.

The mount/path audit covers `$U` at both AWS prefixes, `$NX` at `$X`, `$NR` at `$X/runs`, units, frame roots, models, the closure, epochs and the new job-directory bind. The admission child stages all existing sources before the post-admission block. The runtime-record read uses the staged physical path; the loader receives the namespace path. `tk_pythonpath p` uses `$X/b`, the closure, its site alias and the optional NumPy overlay. The `c`, `t` and `u`-only FLA branch is outside this CPU proof. Both NumPy branches pass the fixture.

The loader command receives `$PILOT_VENV/bin/python` and `$X`. Its Python entry reads the pinned launch/config and admission outputs, then writes `inputs/l.json` and `inputs/a.json` through the existing run mount. After shell success, `verify_prepared` validates `data_receipt.json` through the physical run path. Proof `main()` checks the loader receipt's identity, hash and required predicates, then writes the already reserved job receipt under `kh/o`. No later shell expansion depends on a child export. These predicates and trainer bytes retain their existing definitions.

{validation}

`proof/POST_ADMISSION_SHELL.json` records two successful nounset executions. Each runs the generated suffix, sources the exact production `c.sh` (SHA256 `900d05353901d661474ffa12562d17bebafc4af1f95e03743e348d5ebefb9598`), executes its real helpers, reaches a stub loader import/call and writes a fixture receipt through the proof's real `execute()` function. The fixture supplies a fake allocation, stub admission, stub bwrap and stub loader body. It remaps path constants after sourcing instead of creating a real namespace. Mutation cases remove each required export, precreate or symlink the job directory, and alter runtime bytes; every case refuses before the loader.

`proof/RESEAL11.json` records a successful seal against a local production-form deployment fixture. The archive test checks every member hash and decodes the embedded script to verify exact equality with the generated proof program. It does not issue production authority. The archive name derives from its payload SHA256 so a proof-only change retains config and deployment paths while producing a distinct archive.

Reviewer checks: inspect the environment initialization and namespace mapping; verify the unchanged config, trainer, `c.sh`, `r.sh`, `p0.sh`, job entry and `jb.sh`; verify the new archive SHA and embedded proof; deploy the corrected script and reseal the authority against its new `bundle_files` hash before any approved CPU proof. Bundle and kit names remain `i_69d2930d` and `x_69d2930d`; the archive filename is independent of those names. The failed job receipt remains failed. A complete production loader audit and proof receipt remain unverified locally. No Orchard, SSH, Git or GPU action was performed.

`FIX11.diff` compares packet tools, tests, configs, current bundle, proof evidence and reports with `snap_fac07052`. It omits unchanged archives and transient work fixtures; binary additions carry hashes. Existing `out/p_*.tar` hashes are checked against `FIX11_PROTECTED_ARCHIVES.json`. Snapshot and packet B bytes were not edited. The snapshot comparison is retained because the brief explicitly requires it.
'''
    (out/'FIX11.md').write_text(text)
    (ROOT/'STATUS.md').write_text(f'{status}. Packet A config {binding["config_identity"]}, run {binding["run_key"]}, archive {op["archive"]}, SHA256 {op["sha256"]}. '
        f'The proof exports TK_JOBDIR, R1_RUNTIME_RECORD and TK_RUNS_DIR. {validation} Read out/FIX11.md and out/FIX11.diff. Production proof remains pending.\n')
    names = set()
    for folder in ('tools', 'tests', 'configs', 'out/operator', 'out/proof', 'out/records', 'out/units'):
        for base in (ROOT, SNAP):
            names.update(str(p.relative_to(base)) for p in (base/folder).rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts)
    names.update(str(p.relative_to(ROOT)) for p in out.iterdir()
                 if p.is_file() and p.suffix != '.tar' and p.name not in ('FIX11.diff', 'SHA256SUMS'))
    names.add('STATUS.md')
    patches = []
    for name in sorted(names):
        before, after = SNAP/name, ROOT/name
        a = before.read_bytes() if before.is_file() else b''
        b = after.read_bytes() if after.is_file() else b''
        if a == b: continue
        try:
            if b'\0' in a+b: raise UnicodeError()
            patches.extend(difflib.unified_diff(a.decode().splitlines(keepends=True),
                b.decode().splitlines(keepends=True), fromfile='a/'+name, tofile='b/'+name))
        except UnicodeError:
            patches.append(f'Binary {name}: before={sha(before) if before.is_file() else "absent"} after={sha(after) if after.is_file() else "absent"}\n')
    patches.append(f'Added archive out/{op["archive"]}: SHA256 {op["sha256"]}\n')
    (out/'FIX11.diff').write_text(''.join(patches))
    files = [p for folder in ('proof', 'records', 'units', 'logs') for p in (out/folder).rglob('*') if p.is_file()]
    files += [p for p in out.iterdir() if p.is_file() and p.name != 'SHA256SUMS'
              and (p.suffix != '.tar' or p.name in (op['archive'], 'r1p_code.tar'))]
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in sorted(set(files))))
    print(json.dumps(load(out/'FIX11_RESULT.json'), sort_keys=True))


if __name__ == '__main__':
    main()

"""Write the bounded launch-readiness report from verified receipts."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
KIT=ROOT/'sb_mask_phrase'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()


def line(file,needle):
    return next(i for i,s in enumerate((ROOT/file).read_text().splitlines(),1) if needle in s)


def loc(file,needle): return f'{file}:{line(file,needle)}'


def main():
    files=[OUT/n for n in ('CPU_VALIDATION.json','STAGING_PART2.json','LAUNCHER_TESTS.json','STAGED_SMOKE.json')]
    cpu,stage,tests,smoke=[json.loads(p.read_text()) for p in files]
    assert all(x['status']=='PASS' for x in (cpu,stage,tests,smoke))
    code=KIT/'part2'; launch='sb_mask_phrase/part2/launch_gpu.py'; sam='sb_mask_phrase/part2/sam3_pass.py'
    checks=[
      ('placement and one 48 GB card off trinity-0-13',loc(launch,'def reading'), 'small-card, placement and identity tests'),
      ('two empty nvidia-smi readings 300 seconds apart',loc(launch,"receipt['readings'].append(sample(card))"),'fake nvidia-smi: busy first/second, graphics process, 1024 MiB boundary; wait argument 300'),
      ('vnice',loc(launch,"command = ['timeout'"),'command vector and tampered-vendor tests; local vnice and monitor pinned'),
      ('timeout at remaining budget',loc(launch,'deadline = start'),'fake pass: 4320 s then 4308 s; clean resume subtracts 12 s'),
      ('1.2 GPU-hour hard stop',loc('sb_mask_phrase/part2/watchdog.py','def call_watchdog'),'stalled-call and remaining-budget tests; outer SIGKILL timeout bounds native stalls without a grace period'),
      ('KILLED never rerun',loc(launch,'def admit_state'),'RUNNING, STOP, KILLED, unmarked partial and nonzero-exit tests; clean-end receipt precedes marker rename'),
      ('writes only under GPU output directory',loc(launch,'def environment'),'fake pass write-tree check; TIMING_RECEIPT, logs, caches and vnice control stay in pool_part2'),
      ('bars-first and existing score refusal',loc(launch,"check('pass', kit)"),'missing/altered bars and planted score tests; gate.py and BARS bytes unchanged'),
      ('STEP5 gates the pool pass',loc(sam,"assert gate['status'] == 'PASS'"),'part 2 suite and expected CPU CUDA refusal; default launcher runs STEP5 then pass under one budget')]
    pins={str(p):sha(p) for p in [*files,*sorted(code.glob('*.py')),code/'launch_gpu.sh',code/'gpu_inner.sh',code/'vendor/vnice.sh',code/'vendor/terminator.sh',code/'vendor/PINS.json',Path(__file__)]}
    audit=dict(status='CPU_VERIFIED_LAUNCH_READY',gpu='NOT RUN',method='CPU fake-device and fake-pass tests plus staged import/plan smoke; no process termination tested',
               checks=[dict(check=n,status='PASS',evidence=f'{l}; {t}') for n,l,t in checks],input_sha256=pins)
    (OUT/'GPU_LAUNCH_AUDIT.json').write_text(json.dumps(audit,indent=1)+'\n')
    env=stage['groups']['sam_environment']; default=stage['estimates']['default']; aliases=stage['estimates']['all_aliases']
    timing_location = loc(sam, "(OUT/'TIMING_RECEIPT.json')")
    text=[
      '# PH2FIX report',
      'CPU-VERIFIED LAUNCH-READY. No GPU inference, network, SSH, Git, process termination or external writes ran.',
      f"Tests: part 1 {cpu['part1_tests']}/26; part 2 {cpu['part2_tests']}/20; launcher {tests['ran']}/{tests['ran']}; CPU dry-run steps 1–4 PASS.",
      'Test command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 nice -n 10 python -B verify_cpu.py`; CPU_VALIDATION.json records child commands and evidence hashes.',
    ]
    text += [f'{n}: {l}; PASS — {t}.' for n,l,t in checks]
    text += [
      f"Watchdog: {loc(sam,'@bounded')}; load, encode, detect and STEP5 reader calls use min(300 s, remaining budget). Python alarms interrupt cooperative stalls; outer timeout bounds native stalls.",
      'Timeout exits were simulated with a fake pass; no live process was killed during CPU validation.',
      f"Output path: {timing_location}; all GPU JSON receipts pin their direct controls and the staging manifest, which pins the payload.",
      f"Bars SHA256: {sha(code/'BARS_PART2.json')}; guard SHA256: {sha(code/'gate.py')}; command: `sha256sum sb_mask_phrase/part2/{{BARS_PART2.json,gate.py}}`.",
      f"Pinned vnice SHA256: {sha(code/'vendor/vnice.sh')}; command: `sha256sum sb_mask_phrase/part2/vendor/vnice.sh`; vendor/PINS.json also pins the confined monitor.",
      f"Staging: {stage['files']:,} files, {stage['bytes']:,} bytes = {stage['GB']:.6f} decimal GB; STAGING_PART2.tsv/json lists source paths, staged paths and SHA256.",
      f"SAM3 environment: {stage['environment']}; {env['files']:,} files, {env['bytes']:,} bytes. The staged environment includes SciPy 1.14.1 from p1cpu; the editable SAM3 import resolves inside payload; Linux/NVIDIA driver and shell utilities remain host prerequisites.",
      'Staging commands: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B stage_payload.py`; `python -B relocate_environment.py`; `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B supplement_environment.py`; `bash sb_mask_phrase/run.sh part2/staging.py`.',
      f"Staged smoke PASS: {smoke['captures']} captures, {smoke['decoded_frames']} decoded frames; external application inputs and network blocked; exact command in STAGED_SMOKE.json.",
      f"Default GPU need: one >=48 GB bf16 card; {default['calls']:,} calls × 32 frames × 0.064 GPU-s / 3600 = {default['gpu_h']:.6f} GPU-h.",
      f"--all-aliases GPU need: same card; {aliases['calls']:,} calls × 32 × 0.064 / 3600 = {aliases['gpu_h']:.6f} GPU-h; command producing both estimates: `bash sb_mask_phrase/run.sh part2/staging.py`.",
      'Both estimates exclude loading, STEP5 and encoding; the shared 1.2 GPU-h hard stop includes them. Projection may drop new phrases or stop; completion within budget is not claimed.',
      f'Exact launch command on the authorized GPU compute node: `bash {KIT}/part2/launch_gpu.sh --node-local 0` (add `--all-aliases` if required).',
      'The default command runs STEP5 then pass. A clean `--mode step5` may continue with `--mode pass`; STOP, KILLED, orphan RUNNING and completed passes refuse nonzero.',
      'Package command: `bash package.sh`; out/sb_ph2fix.tar contains the staged payload; out/sb_ph2fix.tar.sha256 records its SHA256.',
    ]
    assert len(text)<=40
    (OUT/'PH2FIX_REPORT.md').write_text('\n'.join(text)+'\n')
    (ROOT/'STATUS.md').write_text(f"CPU validation passes: 26 part 1 tests, 20 part 2 tests, {tests['ran']} launcher tests, and dry-run steps 1–4. The complete staged GPU payload occupies {stage['GB']:.6f} GB and passes isolated CPU imports and frame decoding. The launcher enforces card admission, pinned vnice, cumulative timeout, call watchdogs, write confinement and no resume after STOP/KILLED. No GPU pass has run. out/PH2FIX_REPORT.md gives the launch command and evidence; package.sh produces the archive and checksum.\n")


if __name__=='__main__': main()

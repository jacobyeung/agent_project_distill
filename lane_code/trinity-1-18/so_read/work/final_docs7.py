from pathlib import Path
import subprocess
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'out/kit_parity50/README.md';s=p.read_text()
s=s.replace('```bash\n','```bash\nset -euo pipefail\n')
s=s.replace('  --exclude=orchard-community-2 --job-name=ab0123456789\nsrun --ntasks=1 --pty bash --noprofile --norc', '  --exclude=orchard-community-2 --job-name=ab0123456789 \\\n  srun --ntasks=1 --pty bash --noprofile --norc')
s=s.replace('The wait checks at most once per minute,', 'Run the wait on the same host that launched the detached worker. It checks at most once per minute,')
p.write_text(s)
with (L/'work/STATUS.md').open('a') as f:
    f.write(subprocess.check_output(['date','-u'],text=True)+'Round-7 live-job archive, bounded wait, exact SXM admission, evidence pins and selected-export default implemented. All 119 workspace tests pass; round-7 baseline fails 10 assertions and all 11 before-controls reproduce expected results. Real CPU-proof fixture executes tar successfully. Exact results: out/checks/run_checks7.txt. Workspace reduced to 2,812,067,270 bytes by byte-preserving hardlinks of completed pre-task fixtures. Preparing fresh patch application and gate/submit integration.\n')

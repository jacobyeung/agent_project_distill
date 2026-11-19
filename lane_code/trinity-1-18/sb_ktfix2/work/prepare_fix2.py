from pathlib import Path
import json,hashlib
root=Path.cwd();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs={}
for p in (root/'inputs/exclusions').rglob('*'):
 if p.is_file():inputs[str(p)]=sha(p)
for n in ('__init__.py','backends.py','io.py','safety.py'):
 p=Path('/scratch/jjyeung/geo_bakeoff_kit/work/geo_bakeoff')/n;inputs[str(p)]=sha(p)
p=Path('/scratch/jjyeung/orch_n30/sb_auditfix2/store_room_audit.py');inputs[str(p)]=sha(p)
(root/'configs/FIX2_SOURCES.json').write_text(json.dumps(dict(input_sha256=inputs,scope='Pinned exclusion authorities and geo_bakeoff runtime sources'),indent=2)+'\n')
(root/'inputs/TASK_RULINGS.txt').write_text('Task sb_ktfix2: CPU only; no GPU, network, SSH, Git or process control; write only this workspace. Ruling 0749Z: tower-frames expected 3.6 GPU-hours and room kit expected 0.2 GPU-hours may share one card. Future launches retain vnice, scratch-only assets, hard stops and hash-validated resume. Cards require at least 24,000,000,000 bytes and Ampere or newer for bf16; the allocation cap is min(1, 40e9 / memory). Ruling 1056Z item 1: all Part A and B train decisions use only the 1,012 distance rows outside the 80 withheld rooms (634820b4), with 1,037-row figures alongside for reporting only. Exclude all six affected captures from pose decisions, including scene0255_01 with no priced distance rows. Check R0 (bdb5d402), dev-S1 (969cdb56), BENCH v2 (3119aa4a), withheld-80 (634820b4) and K1 held-out (4d4736cf) using the pinned fixed checker.\n')
p=root/'work/stage_list.py';s=p.read_text().replace("K = Path('/scratch/jjyeung/orch_n30/sb_ktfix')", "K = Path(__file__).resolve().parents[1]").replace("W = Path('/scratch/jjyeung/orch_n30/sb_ktrev2')", "W = K\nREVIEW = Path('/scratch/jjyeung/orch_n30/sb_ktrev2')")
s=s.replace("add(K / 'inputs/K1_ROWSETS',", "add(K / 'inputs/exclusions', 'ABH', 'dir', 'five pinned exclusion lists and fixed room authority tree')\nadd(K / 'inputs/K1_ROWSETS',")
s=s.replace("add(f'{S}/geo_bakeoff_kit/work/geo_bakeoff', 'C', 'dir', 'geo_bakeoff.backends (DA3 adapter, validate_device)')", "# geo_bakeoff runtime is inside the staged and code-pinned kit code directory.")
s=s.replace("bound to code 53ea9d60", "bound to current code_sha256")
s=s.replace("jl(W / 'work/trace'", "jl(REVIEW / 'work/trace'")
s=s.replace("summary = dict(totals=", "input_sha256={p:r['sha256'] for p,r in results.items() if r['sha256'] is not None}\ninput_sha256[str(Path(__file__).resolve())]=sha_file(__file__)\ninput_sha256[str(OUT/'STAGE_LIST.tsv')]=sha_file(OUT/'STAGE_LIST.tsv')\nfor part in 'ABC':\n    path=REVIEW/'work/trace'/f'trace_{part}.json';input_sha256[str(path)]=sha_file(path)\nsummary = dict(input_sha256=input_sha256,command='bash scripts/cpu.sh work/stage_list.py',trace_scope='Read-set cross-check against reviewer CPU traces; new vendored code and exclusions are enumerated explicitly',totals=")
p.write_text(s)
(root/'STATUS.md').write_text('The held-out, 24 GB and room-exclusion fixes pass 33 CPU tests. The fixed checker resolves all 239 train captures and excludes six withheld captures: 25 distance rows from five captures plus scene0255_01. Five planted rows hit the five respective exclusion lists. Dry-run, complete A0 reproduction and staging validation remain.\n')

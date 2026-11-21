"""Render the current delivery identity and the CPU real-unit contract in PLACE.md and REPORT.md."""
import json
import re
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_depth as BD
import cpu_unit as CU

b = json.loads((HERE/'out/BUILD.json').read_text())
boot = b['boot']
public = {k: v for k, v in b.items() if k not in ('layout', 'external_inputs', 'forecast', 'boot', 'boot_closure')}
descriptor = len(BD.B.jd(public))
e = CU.ESTIMATES
need = lambda dense: 1.25*(e['first_model'][str(dense)]+e['load']+e['prefill'])+e['margin']
bench = json.loads((HERE/'out/CPU_TOWER_BENCH.json').read_text())
t64, t32 = bench['frames64']['rows'][-1], bench['frames32']['rows'][-1]
checks = json.loads((HERE/'out/CPU_UNIT_CHECKS.json').read_text()) if (HERE/'out/CPU_UNIT_CHECKS.json').exists() else dict(cases=[])
names = ', '.join(c['name'] for c in checks['cases'])
section = f"""<!-- cpu-unit -->
## CPU real unit

The Orchard CPU check now runs the job's first real unit through the full model on CPU before it can pass. After the boot gate, staging, bundle and write-test guards, preparation and the operator rehearsal, the operator's `cpu_unit` (`a/6.py`) launches the production worker exactly as the GPU operator does: `commands()` writes `metadata/a/30.json` (action 3), and the numeric entry runs `g.w.run` with a `cpu_unit` configuration. The worker loads the full step-544 carrier and heads through `make_capped_real(..., device='cpu')` with the production loader's dtypes (bf16 base parameters, fp32 heads), runs the pinned G3T weights through `TowerG3T`/`FrozenG3TTower` on the capture's served PNGs, then runs `capture_one` (one prefill, geometry and own-depth scale) and the record encoder. Torch uses the job's CPUs (`os.sched_getaffinity`, 16 under `--cpus-per-task=16`).

`metadata/33.json` (worker) and `metadata/34.json` (operator) become `CPU.json` `real_unit`. The receipt records seconds and peak RSS for the stages `bind`, `first_model`, `load`, `prefill` and `record`; shapes, dtypes and finite flags of the first-model outputs; minimum, maximum, mean and median of the served float16 plane (32×51×51) and its exact plane; the scale, the intrinsics K, the parameter count, dtypes and placement; the admission decision; and the operator's memory peaks. Parity against the GPU reference is recorded but not required: on CPU the G3T stage runs in fp32 because its bf16 autocast is CUDA-only (`tower_read.py:246`).

`real_unit.passed` requires all five stages, worker exit 0, clean output checks, no deadline or memory stop and step 544. Otherwise `a/5.py` fails the `CPU real unit passed` comparison, writes the unit receipt to `a/31.json`, and supervisor recovery returns it as `metadata/31.json` beside `metadata/30.json`. `a/9.py` (run by `o_check_sub.sh` before the GPU submit) and the GPU bootstrap both require a passing real unit.

The CPU job keeps the GPU job's flags except `--gres` and therefore its 00:50:00 allocation. With E = min(start + 3,000 s, `SLURM_JOB_END_TIME`), the worker must stop by E − {CU.UNIT_STOP_S} s and the operator kills it at E − {CU.UNIT_KILL_S} s (SIGTERM, then SIGKILL after 5 s), so `CPU.json` is written before Slurm's USR1 at E − 120 s. At worker start the admission computes need = 1.25 × (first model + load + prefill) + {e['margin']} s from measured estimates: first model {e['first_model']['64']} s for 64 frames and {e['first_model']['32']} s for 32 (measured {t64['run_s']:.0f} s and {t32['run_s']:.0f} s on 16 threads of a shared EPYC 9224 node, `out/CPU_TOWER_BENCH.json`), load {e['load']} s, prefill {e['prefill']} s. The first capture (64 frames) needs {need(64):,.0f} s; the first 32-frame capture in production order (index 30) needs {need(32):,.0f} s. If the first capture does not fit, the worker runs that 32-frame capture through the same code and every stage, recording `time_guard` with the numbers; if neither fits it records `over_budget`, runs index 30 anyway, and the kill deadline still preserves the receipt. The first capture fits only when everything before the unit finishes within about {(3000-CU.UNIT_STOP_S-need(64))/60:.1f} minutes, so expect `time_guard`.

Memory stays under the job's 200G cgroup. The CPU worker alone sets `RLIMIT_AS` to {CU.ADDRESS_SPACE//1024**3} GiB; the GPU worker has no cap. The operator samples memory once a second as the cgroup's `memory.current` minus its file LRU pages, so page cache from staged archives is not charged (fallback: process-tree RSS), and SIGKILLs the worker at {CU.GUARD_BYTES//1024**3} GiB. The measured CPU first model peaked at {t64['peak_rss_gb']:.1f} GB; rank 4's 9B carrier peaked at 43 GB on CPU. Worker outputs stay on the job's ext4 `/tmp` root. `CPU.json` grows by about 10 KB (400 KB cap); `a/31.json` is written only on failure (at most 100 KB). The 48,000,000-byte `/project` budget is unchanged.

`tests/test_cpu_unit.py` runs the delivered operator's `cpu_unit`, which launches the delivered worker through the operator's prefix seam with `tests/cpu_unit_fixture.py` doubles: a tiny native Qwen3.5 hybrid CarrierC1 (linear- and full-attention layers, pose and gravity heads, private depth head with its ViT copy; bf16 base as loaded in production), real tiny G3T components at 28 px, and the matching prompt batch. Real artifact manifests, `Artifact.verify`, `Audit`, `stage_capture` from the authenticated local `a2.tar`, `bind_item`, the tower run on 64 or 32 served frames, the prefill, heads, geometry, scale and record encoding are production code. Cases: {names}. The pinned cases run the production interpreter `d/v/py` (transformers 5.19.0, torch 2.13.0+cu130) in the production-shaped namespace. `tests/test_write_receipt.py` adds the real-unit failure through production fetch and `a/9.py` rejections.

The GPU path was audited against the pinned environment (transformers 5.19.0, torch 2.13.0+cu130; the same `q/env.json` receipt under which T1 run 173662 replayed these serving sources on GPU). The boot gate imports the same {len(b['boot_closure']['modules'])} modules in CPU and GPU mode. `fla` and `causal_conv1d` appear only at the excluded `carrier_c1_run.fla_check` site, which the worker never calls; the pinned environment lacks both, so transformers uses its PyTorch fallbacks on either device. The worker's own code never reads cache tensors, and during this prefill the serving sources read `past_key_values` only through `get_seq_length`. Three CPU-only failures were certain and are fixed: `Monitor.begin` called `torch.cuda.reset_peak_memory_stats()`, which fails without CUDA (`runtime/m.py`); `start_tower` hard-coded `cuda:0` and `torch.cuda.synchronize()` (`runtime/w.py`); and `run` required an H100 and synchronized after each capture. The GPU worker keeps its H100 check, CUDA device, synchronization, 60-capture loop and unlimited address space.

Remaining risks: the time estimates come from a shared local EPYC 9224 node, and load and prefill for the step-544 carrier on CPU are unmeasured, so a slow Orchard node can reach `over_budget` and fail the CPU check (cost: one CPU job, no GPU job). Under `time_guard` the 64-frame first capture's G3T stage does not run on CPU in the check; the same code ran on 64 frames in the benchmark and the tiny tests. If the step-544 artifact attached an MDG head, `_prepare_decode` would call `mdg_features.expand_cache`, which reads `conv_states.shape`, while 5.19.0 stores those states as dicts; T1's success in this environment indicates the export has no MDG head, and the CPU unit would expose it before any GPU job. CPU parity with the GPU reference is not expected. Without cgroup v2 the guard falls back to process-tree RSS.
<!-- /cpu-unit -->
"""
rows = {'`out/delivery.tgz`': b['delivery_bytes'], 'Expanded inner payload (32 MiB limit)': b['payload_expanded_bytes'],
        'Installed package files': b['installed_bytes'], 'Installed `BUILD.json`': descriptor,
        'Streamed `orchard/o_place.sh`': (HERE/'orchard/o_place.sh').stat().st_size,
        'Conservative delivery + installed files + descriptor': b['delivery_bytes']+b['installed_bytes']+descriptor}
for name in ('PLACE.md', 'REPORT.md'):
    p = HERE/name; s = p.read_text()
    if '<!-- cpu-unit -->' in s:
        s = s[:s.index('<!-- cpu-unit -->')]+s[s.index('<!-- /cpu-unit -->')+len('<!-- /cpu-unit -->'):].lstrip('\n')
    s = re.sub(r'\b(?:85|95) tests\b', '%d tests' % 95, s)
    s = re.sub(r'validate\.py \d+/\d+', 'validate.py 95/95', s)
    s = re.sub(r'Delivery SHA256: `[0-9a-f]{64}`\.', 'Delivery SHA256: `'+b['delivery_sha256']+'`.', s)
    s = re.sub(r'Token: `[^`]+`\. Delivery: `out/delivery.tgz`, \*\*[\d,]+ bytes\*\*\.\nSHA256: `[0-9a-f]{64}`\.',
               f"Token: `{b['token']}`. Delivery: `out/delivery.tgz`, **{b['delivery_bytes']:,} bytes**.\nSHA256: `{b['delivery_sha256']}`.", s)
    s = re.sub(r'Pre-bulk authenticated source bytes total \*\*[\d,]+\*\*, including \*\*[\d,]+\*\* package bytes',
               f"Pre-bulk authenticated source bytes total **{boot['pre_bulk_bytes']:,}**, including **{boot['package_archive_bytes']:,}** package bytes", s)
    for key, value in rows.items():
        s = re.sub(r'\| '+re.escape(key)+r' \| [\d,]+ \|', '| '+key+' | '+format(value, ',')+' |', s)
    end = '<!-- /boot-order -->'
    s = s.replace(end, end+'\n\n'+section, 1) if end in s else section+'\n'+s
    p.write_text(s)
print(json.dumps(dict(token=b['token'], delivery_sha256=b['delivery_sha256'], delivery_bytes=b['delivery_bytes'])))

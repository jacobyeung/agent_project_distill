"""Calculate launch intervals from the two supplied job traces."""
from datetime import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRROR = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
FILES = {'A': MIRROR / 'swarm_opt/work/o/look1.out', 'C': MIRROR / 'r1_ops6/work/mon/last.txt'}
OUT = ROOT / 'out/evidence'
OUT.mkdir(exist_ok=True)

def seconds(start, end):
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()

intervals = [
    ('submit_to_wrapper', 'C', '2026-11-18T22:18:18+00:00', '2026-11-18T22:20:34+00:00', 'supplied submit time; raw wrapper timestamp'),
    ('wrapper_to_preflight_stage', 'C', '2026-11-18T22:20:34+00:00', '2026-11-18T22:20:44+00:00', 'raw timestamps'),
    ('wrapper_to_preflight_stage', 'A', '2026-11-18T02:13:17+00:00', '2026-11-18T02:13:19+00:00', 'raw timestamps'),
    ('preflight', 'C', '2026-11-18T22:20:44+00:00', '2026-11-18T22:21:57+00:00', 'raw timestamps and seconds=73'),
    ('preflight', 'A', '2026-11-18T02:13:19+00:00', '2026-11-18T02:13:55+00:00', 'raw timestamps and seconds=36'),
    ('preflight_to_stage', 'C', '2026-11-18T22:21:57+00:00', '2026-11-18T22:33:12+00:00', 'measured timestamps; three checkpoint verifications inferred from native call sites'),
    ('preflight_to_stage', 'A', '2026-11-18T02:13:55+00:00', '2026-11-18T02:13:56+00:00', 'raw timestamps'),
    ('stage_before_frames', 'C', '2026-11-18T22:33:12+00:00', '2026-11-18T22:40:48+00:00', 'raw timestamps'),
    ('stage_before_frames', 'A', '2026-11-18T02:13:56+00:00', '2026-11-18T02:21:12+00:00', 'raw timestamps'),
    ('stage_frames_envelope', 'C', '2026-11-18T22:40:48+00:00', '2026-11-18T23:04:40+00:00', 'raw timestamps; extraction plus verification'),
    ('stage_frames_envelope', 'A', '2026-11-18T02:21:12+00:00', '2026-11-18T02:44:33+00:00', 'raw timestamps; extraction plus verification'),
    ('stage_init', 'C', '2026-11-18T23:04:40+00:00', '2026-11-18T23:04:55+00:00', 'raw timestamps'),
    ('stage_init', 'A', '2026-11-18T02:44:33+00:00', '2026-11-18T02:44:48+00:00', 'raw timestamps'),
    ('native_mode_p', 'C', '2026-11-18T23:04:55+00:00', '2026-11-19T01:25:29+00:00', 'raw timestamps'),
    ('native_mode_p', 'A', '2026-11-18T02:44:48+00:00', '2026-11-18T05:10:04+00:00', 'raw timestamps'),
    ('prepare_to_result_mtime', 'C', '2026-11-18T23:04:55+00:00', '2026-11-19T00:15:17+00:00', 'inferred from PROMPT.md supplied result.json mtime'),
    ('prepare_to_result_mtime', 'A', '2026-11-18T02:44:48+00:00', '2026-11-18T03:58:00+00:00', 'inferred from PROMPT.md approximate prepare completion'),
    ('post_prepare_to_exit', 'C', '2026-11-19T00:15:17+00:00', '2026-11-19T01:25:29+00:00', 'inferred residual; includes native revalidation and frame audit'),
    ('post_prepare_to_exit', 'A', '2026-11-18T03:58:00+00:00', '2026-11-18T05:10:04+00:00', 'inferred residual using approximate completion'),
    ('mode_p_to_second_stage', 'C', '2026-11-19T01:25:29+00:00', '2026-11-19T01:26:55+00:00', 'measured timestamps; fourth checkpoint verification inferred from parent guard'),
    ('mode_p_to_second_stage', 'A', '2026-11-18T05:10:04+00:00', '2026-11-18T05:10:05+00:00', 'raw timestamps'),
    ('second_stage', 'C', '2026-11-19T01:26:55+00:00', '2026-11-19T01:29:17+00:00', 'raw timestamps'),
    ('second_stage', 'A', '2026-11-18T05:10:05+00:00', '2026-11-18T05:12:13+00:00', 'raw timestamps'),
    ('train_to_binding_mirror', 'C', '2026-11-19T01:29:17+00:00', '2026-11-19T01:40:13+00:00', 'raw timestamps; overlaps beginning of optimizer step'),
    ('train_to_binding_mirror', 'A', '2026-11-18T05:12:13+00:00', '2026-11-18T05:21:19+00:00', 'raw timestamps; overlaps beginning of optimizer step'),
    ('submit_to_first_persisted_step', 'C', '2026-11-18T22:18:18+00:00', '2026-11-19T01:47:02+00:00', 'PROMPT.md supplied submit/first-step timestamps'),
]
data = [dict(phase=phase, job={'A':'171377','C':'172660'}[job], start=start, end=end,
             seconds=seconds(start,end), minutes=round(seconds(start,end)/60, 4), evidence=evidence)
        for phase, job, start, end, evidence in intervals]
(ROOT / 'out/phase_timing.json').write_text(json.dumps(data, indent=2) + '\n')
with (OUT / 'startup_log_excerpts.txt').open('w') as out:
    for label, source in FILES.items():
        out.write(str(source) + '\n')
        lines = source.read_text().splitlines()
        for i, line in enumerate(lines, 1):
            keep = ((label == 'A' and (271 <= i <= 280 or 328 <= i <= 371 or 397 <= i <= 407))
                    or (label == 'C' and (153 <= i <= 166 or 210 <= i <= 250)))
            if keep:
                out.write(str(i) + ': ' + line + '\n')
for row in data:
    print(row['job'], row['phase'], row['seconds'], 's', row['minutes'], 'min', row['evidence'])

<!-- recovered by seal_plan: transcript=71f94277 line=15497 utc=2026-11-12T23:10:49.810Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s - <<'PYEOF'
import os
f = '/data3/jjyeung/mover_20261111/DISCUSSION.md'
t = open(f).read()
a = t.rindex('wait for the user\'s word on Mind traffic."')
b = a + len('wait for the user\'s word on Mind traffic.')
junk = t[b:]
assert junk.startswith('" >> /data3/jjyeung/mover_20261111/DISCUSSION.md; echo "') and junk.rstrip().endswith('ORCH_HANDOFF.md'), junk[:80]
t = t[:b] + '\n'
open(f + '.next', 'w').write(t); os.replace(f + '.next', f)
print('fixed; tail:', t[-160:])
PYEOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: ruled on 0-13 orch_cd/derivgen (165 GB) in the mover's DISCUSSION.md: REMOVE out/v3_sources_*, scale_sources_*, v3_scenes_*, mesh_copy_01 (~75 GB; rebuildable intermediates, public mesh copy); ARCHIVE-THEN-REMOVE v3_publish_*, scale_publish_*, derivgen5_parent, extra_scenes_01, inputs/, GENERATOR tars, review pools (~76 GB; training-row provenance for the dataset release); unmatched names KEEP until listed. (My first write of this entry carried a shell fragment into DISCUSSION.md through a misplaced heredoc terminator; removed within a minute.)" >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md
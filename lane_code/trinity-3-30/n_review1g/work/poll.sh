B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; S=/scratch/jjyeung/orch_n30/n_review1g
M=$S/work/.mark; [ -f $M ] || touch -d '2026-11-20 05:15 UTC' $M
date -u +%TZ
for d in n_review tree_rebuild n_ops fb_pack; do for f in $(ls -t $B/events/$d | head -15); do [ "$B/events/$d/$f" -nt $M ] && [ "$f" != STATUS.md ] && echo "NEW $d/$f"; done; done
for f in $(ls -t $S/inbox); do [ $S/inbox/$f -nt $M ] && echo "INBOX $f"; done
touch $M

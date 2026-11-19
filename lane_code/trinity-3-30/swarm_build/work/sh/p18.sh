R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p
for w in sb_ktchk3 sb_fhrev; do tmux has-session -t $w 2>/dev/null && echo "$w alive" || echo "$w ended"; ls $w/REVIEW_VERDICT.md 2>/dev/null; find $w -newermt '-10 min' -type f 2>/dev/null | grep -v -E 'extract|tmp' | wc -l; tail -c 200 $w/cursor.log; echo; done
awk -F'|' '{s+=$6; n++} END {print n, s}' $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log
sha256sum $R/sb_fhalias/out/ALIAS.patch

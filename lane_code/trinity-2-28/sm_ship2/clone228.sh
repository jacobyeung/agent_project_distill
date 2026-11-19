#!/bin/bash
set -u
S=/scratch/jjyeung/distill_sync; I=/scratch/jjyeung/orch_n30/sm_ship2; BU=/scratch/jjyeung/distill_sync_init/lane-code.bundle
hostname -s; date -u
sha256sum $BU | cut -c1-16
if [ ! -d $S/repo/.git ]; then
  mkdir -p $S
  nice -n 10 git bundle verify $BU 2>&1 | tail -2
  nice -n 10 git clone -q --branch lane-code $BU $S/repo 2>&1 | tail -3
  cp $S/repo/.git/config $S/repo_config.from_bundle
  cp $I/state/git_config $S/repo/.git/config
  for f in LCS_ROBUST_BUDGETS PUSH_DONE.txt PUSH_REFUSED.txt KITS_LANDED.txt; do cp -n $I/state/$f $S/$f; done
  touch $S/LCS_ROBUST_SYNC; chmod 600 $S/LCS_ROBUST_SYNC; mkdir -p $S/flagged
fi
git -C $S/repo branch -vv | head -3
git -C $S/repo remote -v
echo "HEAD $(git -C $S/repo rev-parse HEAD)"
echo "GITHUB $(timeout 60 git -C $S/repo ls-remote origin refs/heads/lane-code)"
git -C $S/repo status --porcelain -uno | head -3; echo porcelain_done
du -sh $S/repo; df -h /scratch | tail -1; ls -la $S
for t in filter move; do echo "== $t"; tail -c 600 /scratch/jjyeung/orch_n30/sm_$t/codex.log; cat /scratch/jjyeung/orch_n30/sm_$t/work/STATUS.md 2>/dev/null | tail -5; ls /scratch/jjyeung/orch_n30/sm_$t/out; done
date -u

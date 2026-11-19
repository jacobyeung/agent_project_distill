set -u
R=/scratch/jjyeung/distill_sync/repo; BU=/scratch/jjyeung/distill_sync_init/inc1.bundle
cat > $BU; ls -l $BU | cut -c1-120
git -C $R bundle verify $BU 2>&1 | tail -1
git -C $R fetch -q $BU refs/remotes/origin/main:refs/remotes/origin/main 2>&1 | tail -2
git -C $R fetch -q $BU lane-code 2>&1 | tail -2
git -C $R merge -q --ff-only FETCH_HEAD 2>&1 | tail -2
echo "HEAD $(git -C $R rev-parse HEAD) MAIN $(git -C $R rev-parse refs/remotes/origin/main)"
echo "GITHUB $(timeout 60 git -C $R ls-remote origin refs/heads/lane-code)"
git -C $R status --porcelain -uno | head -3; echo porcelain_done

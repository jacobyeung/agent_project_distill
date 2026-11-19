export PKG=/scratch/jjyeung/so_syncfix_delivery
export B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
export S=/scratch/jjyeung/distill_sync
nice -n 10 bash <<'INSTALL'
set -eu
exec 8>"$S/.sync.lock"
flock -n 8 || { echo 'An existing sync holds the lock; installation deferred.'; exit 3; }
(cd "$B" && sha256sum -c "$PKG/PREIMAGE.sha256")
if [ -e "$B/tools/lane_code_stage.sh" ] || [ -L "$B/tools/lane_code_stage.sh" ]; then
  echo 'The new helper path already exists; reconcile it before installation.'; exit 2
fi
patch --dry-run --forward --batch --fuzz=0 -p1 -d "$B" < "$PKG/INSTALL_TOOLS.diff"
patch --forward --batch --fuzz=0 --no-backup-if-mismatch -p1 -d "$B" < "$PKG/INSTALL_TOOLS.diff"
(cd "$B" && sha256sum -c "$PKG/POSTIMAGE.sha256")
for file in lane_code_sync.sh lane_code_stage.sh tssh.sh; do
  bash -n "$B/tools/$file"
done
INSTALL

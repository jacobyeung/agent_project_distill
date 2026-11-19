#!/bin/bash
# Saved owner script: bash -eu /path/to/so_syncfix/disable.sh /absolute/install-backups/<id>
# rollback.sh sources this script so descriptor 8 remains locked through restoration.
date -u
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
B=${B:-/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30}
S=${S:-/scratch/jjyeung/distill_sync}
PYTHON=${LCS_OWNER_PYTHON:-/usr/bin/python3}
PKG=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
[ "$(hostname -s)" = trinity-3-30 ] || { echo 'DISABLE REFUSED: wrong host' >&2; exit 2; }
[ "${LCS_ROBUST_SYNC:-0}" != 1 ] || { echo 'DISABLE REFUSED: unset the environment activation switch first' >&2; exit 2; }
[ "$#" = 1 ] || { echo 'DISABLE REFUSED: supply the exact install-backup directory printed by install' >&2; exit 2; }
BACKUP=$(cd "$1" && pwd -P)
[ -f "$BACKUP/preimage.tar" ] && [ -f "$BACKUP/PREIMAGE.sha256" ] || {
  echo 'DISABLE REFUSED: backup archive or manifest missing' >&2; exit 2;
}
exec 8>"$S/.sync.lock"
flock -n 8 || { echo 'DISABLE REFUSED: sync holds lock; nothing changed' >&2; exit 3; }
STAMP=$(date -u +%Y%m%dT%H%M%SZ)-$$
for path in "$S/stage" "$S/LCS_ROBUST_SYNC"; do
  [ ! -L "$path" ] || { echo "DISABLE REFUSED: symlink $path" >&2; exit 2; }
done
[ ! -e "$S/stage" ] || [ -d "$S/stage" ] || { echo 'DISABLE REFUSED: stage is not a directory' >&2; exit 2; }
[ ! -e "$S/LCS_ROBUST_SYNC" ] || [ -f "$S/LCS_ROBUST_SYNC" ] || { echo 'DISABLE REFUSED: flag is not regular' >&2; exit 2; }
for path in "$S/stage.pre-robust-$STAMP" "$S/LCS_ROBUST_SYNC.off-$STAMP"; do
  [ ! -e "$path" ] && [ ! -L "$path" ] || { echo "DISABLE REFUSED: existing destination $path" >&2; exit 2; }
done
# Retire stage first: if its move fails, the flag still keeps the legacy path off.
if [ -d "$S/stage" ]; then
  mv -T "$S/stage" "$S/stage.pre-robust-$STAMP"
  printf 'RETAINED %s\n' "$S/stage.pre-robust-$STAMP"
fi
if [ -f "$S/LCS_ROBUST_SYNC" ]; then
  mv -T "$S/LCS_ROBUST_SYNC" "$S/LCS_ROBUST_SYNC.off-$STAMP"
  printf 'RETAINED %s\n' "$S/LCS_ROBUST_SYNC.off-$STAMP"
fi
echo 'DISABLED: the first legacy run rebuilds stage; no retained file was deleted.'
printf 'ROLLBACK: B=%q S=%q bash -eu %q %q\n' "$B" "$S" "$PKG/rollback.sh" "$BACKUP"
date -u

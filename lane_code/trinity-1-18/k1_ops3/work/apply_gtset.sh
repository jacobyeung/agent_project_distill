#!/bin/bash
# Deploy the reviewed gt-set build (codex_gtset) into the executed kit copy kc. Refuses while any K1 phase runs
# or before tower_sam run 2 has ended. usage: apply_gtset.sh [ENDED_BY_ORDER_FILE]
# ENDED_BY_ORDER_FILE: an *_ORCH_*.md in the k1_ops3 events folder that declares tower_sam ended with captures left.
set -euo pipefail
KC=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a
NB=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/kc/k1_build/work/kit_k1a
P=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_pre_gtset
OUT=/scratch/jjyeung/k1/run_tower_sam_2
EV=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3
die(){ echo "REFUSED: $*" >&2; exit 2; }
h(){ sha256sum "$1" | cut -c1-64; }

if pgrep -u "$(id -u)" -f 'kit_k1a/work/(k1_pipeline|watchdog|k1_cli)\.py|kit_k1a/work/run_k1\.sh' >/dev/null; then
  die "a K1 phase process runs from kit_k1a: $(pgrep -u "$(id -u)" -af 'kit_k1a/work/(k1_pipeline|watchdog|k1_cli)\.py|kit_k1a/work/run_k1\.sh' | cut -c1-120 | tr '\n' ';')"
fi
if ! grep -q '"event": "complete"' "$OUT/PROGRESS.jsonl"; then
  [ $# -eq 1 ] || die "tower_sam run 2 has no complete event and no ORCH order file was given"
  case "$1" in "$EV"/*_ORCH_*.md) [ -f "$1" ] || die "order file $1 does not exist";; *) die "order file must be an *_ORCH_*.md in $EV";; esac
  echo "tower_sam ended by order: $1"
fi
[ -e "$OUT/STOP" ] && [ "$(cat "$OUT/STOP")" = RESUME ] && die "run root STOP file says RESUME"

declare -A BEFORE=(
 [work/k1_cli.py]=3cc7b95ff591d68dc0184ac76d7b706a3b7920c94a2132b0eedd99c1c7e49013
 [work/k1_pipeline.py]=46c10147710bf7e8d087c51147464cce72cfc3cff10c89f20a4ddb6bcad76111
 [work/k1_report.py]=607a8a16f9a42b88bbc5e7f36aafb0bc6b700507f269a914ca4c84f2bcb9136a
 [work/refit/train.py]=57fff4ec9158afe83e6990280efc87bb53ac8eae0465232b26d1eeb1a4af8f44
 [out/DEPENDENCIES.json]=b27c28c4fc8c32299dda66d470644c7f6d1b574492fe81a767e601f1b47b91e2)
declare -A AFTER=(
 [work/gt_set.py]=5d36d1ea98c14b2e3181a4571a87dc81efa980bd88a2302e27a1ecc13833a4f8
 [work/k1_cli.py]=f14df4eda722337e0e7187a759e287eed79bb3201b03ffef351591ce5241c0da
 [work/k1_pipeline.py]=deb51a265425e092870c7eadb2fd498b5942b466bb759b39c84fa96e0c762157
 [work/k1_report.py]=14b35f83184267f85a946079767d7903d3e1c31d73946bd2600bbe6b2efe862d
 [work/refit/train.py]=4087716014ab26e7fdb91f336e3d8ee81f97e82b85a4c340376e872c655ecfef
 [out/DEPENDENCIES.json]=aa0a728148bbf076fe1d42a6fe4bb053c761052ec653faa02f7a06e240b8ca42)
ORDER=(work/gt_set.py work/k1_cli.py work/k1_pipeline.py work/k1_report.py work/refit/train.py out/DEPENDENCIES.json)

[ -e "$KC/work/gt_set.py" ] && die "kc already has work/gt_set.py"
[ -e "$P" ] && die "backup folder $P already exists"
for f in "${!BEFORE[@]}"; do [ "$(h "$KC/$f")" = "${BEFORE[$f]}" ] || die "live $f differs from its before hash"; done
for f in "${ORDER[@]}"; do [ "$(h "$NB/$f")" = "${AFTER[$f]}" ] || die "build $f differs from its reviewed hash"; done

mkdir -p "$P/work/refit" "$P/out"
for f in "${!BEFORE[@]}"; do cp -p "$KC/$f" "$P/$f"; [ "$(h "$P/$f")" = "${BEFORE[$f]}" ] || die "backup of $f differs"; done
for f in "${ORDER[@]}"; do
  cp "$NB/$f" "$KC/$f.part"; [ "$(h "$KC/$f.part")" = "${AFTER[$f]}" ] || die "copy of $f differs"
  mv "$KC/$f.part" "$KC/$f"; echo "applied $f ${AFTER[$f]}"
done
for f in "${ORDER[@]}"; do [ "$(h "$KC/$f")" = "${AFTER[$f]}" ] || die "deployed $f differs"; done
cd "$KC" && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_sources.py
echo "APPLIED $(date -u +%FT%TZ); originals in $P"

<!-- recovered by seal_plan: transcript=71f94277 line=21067 utc=2026-11-13T12:58:55.032Z kind=written original_path=/scratch/jjyeung/orch_cd/scratch_0_13/out/RUN_2_18_REMOVALS.sh  -->
#!/usr/bin/env bash
# RULED: REMOVE by the orchestrator (orch-home-distill-79, 2026-11-13T12:59Z).
# One row on trinity-2-18: the extracted copy of the paid Argon outputs that was brought over from trinity-0-13.
# It is a duplicate: the archive beside it (argon_traces_onlycopy_20261113.tar) was made from it and verified
# (82,710 members; sha256 below), and the source is still on trinity-0-13. This script re-hashes that archive
# before it touches anything and refuses if the hash differs.
#
# For the user only, on trinity-2-18.
# Usage: bash RUN_2_18_REMOVALS.sh          (check only: archive hash and folder size, no change)
#        bash RUN_2_18_REMOVALS.sh --go     (check, then remove the duplicate folder)
set -uo pipefail
[ "$(hostname -s)" = "trinity-2-18" ] || { echo "REFUSE: host is $(hostname -s), not trinity-2-18"; exit 1; }
GO=0; [ "${1:-}" = "--go" ] && GO=1

F=/scratch/jjyeung/orch_cd/from_0_13
TAR="$F/argon_traces_onlycopy_20261113.tar"
WANT_SHA=4d60ce496deeb975fb2b8154dd1396eacfffae2f42be766317f5137f5dc2e2da
WANT_BYTES=16167024640
P="$F/argon_traces"
WANT_MIB=15557

echo "## before: $(date -u +%FT%TZ)"; df -B1G /scratch
[ -f "$TAR" ] || { echo "REFUSE: archive missing: $TAR"; exit 1; }
got_bytes=$(stat -c %s "$TAR")
[ "$got_bytes" = "$WANT_BYTES" ] || { echo "REFUSE: archive is $got_bytes bytes, expected $WANT_BYTES"; exit 1; }
got_sha=$(nice -n 19 ionice -c3 sha256sum "$TAR" | cut -d' ' -f1)
[ "$got_sha" = "$WANT_SHA" ] || { echo "REFUSE: archive sha256 $got_sha differs from $WANT_SHA"; exit 1; }
echo "OK archive verified: $TAR"
if pgrep -af 'from_0_13/argon_traces' | grep -v -E 'pgrep|RUN_2_18_REMOVALS'; then
  echo "REFUSE: a process references the folder"; exit 1
fi
if [ ! -d "$P" ] || [ -L "$P" ]; then echo "SKIP missing or symlink: $P"; exit 0; fi
got=$(nice -n 19 ionice -c3 du -x -s -B1M "$P" | cut -f1)
lo=$(( WANT_MIB * 95 / 100 )); hi=$(( WANT_MIB * 105 / 100 + 1 ))
if [ "$got" -lt "$lo" ] || [ "$got" -gt "$hi" ]; then echo "SKIP size $got MiB, expected $WANT_MIB: $P"; exit 0; fi
echo "OK $got MiB: $P"
if [ "$GO" = 1 ]; then nice -n 19 ionice -c3 rm -rf --one-file-system -- "$P" && echo "REMOVED $P"; fi
echo "## after: $(date -u +%FT%TZ)"; df -B1G /scratch

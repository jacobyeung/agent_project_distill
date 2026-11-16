#!/bin/bash
# Wheels (sdists where no wheel exists) for the simulator env e_lb on CPython 3.10 / manylinux x86_64, from its freeze,
# into $V/dl/wheels_lb310 (for a CPU-only copy of the env elsewhere). Login node, network-bound.
set -uo pipefail; V=/project/community/jjyeung/vla_libero; D=$V/dl/wheels_lb310; mkdir -p $D; export PIP_CACHE_DIR=$V/cache/pip
P=$V/envs/e_sv/bin/python; X=(--extra-index-url https://download.pytorch.org/whl/cpu)
while read -r req; do
  [ -z "$req" ] && continue
  $P -m pip download -q --no-deps -d $D "$req" --python-version 3.10 --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux_2_28_x86_64 --only-binary=:all: "${X[@]}" 2>/dev/null \
    || $P -m pip download -q --no-deps --no-binary=:all: -d $D "$req" 2>/dev/null || echo "MISSING $req"
done < $V/dl/lb.txt
$P -m pip download -q --no-deps -d $D websockets==16.1.1 msgpack==1.2.4 --python-version 3.10 --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --only-binary=:all: 2>/dev/null
cd $D && sha256sum * > ../wheels_lb310.sha256; echo "WHEELS $(ls | wc -l) files $(du -sh . | cut -f1)"

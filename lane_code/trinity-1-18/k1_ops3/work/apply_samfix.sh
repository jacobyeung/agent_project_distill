#!/bin/bash
# Apply the reviewed samfix to the kit copy (never the mirror), then verify pins.
set -e
KC=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a; F=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_samfix
mkdir -p /scratch/jjyeung/orch_n30/k1_ops3/work/kc_pre_samfix
cp -p $KC/native_kit/boundaries.py $KC/out/DEPENDENCIES.json /scratch/jjyeung/orch_n30/k1_ops3/work/kc_pre_samfix/
[ "$(sha256sum $F/patched/native_kit/boundaries.py | cut -c1-64)" = 5fbe3ae6ace471c8d8ec532cdde50b0bca4db687b5fc5f7c890c9b6ad44e620c ]
[ "$(sha256sum $F/DEPENDENCIES.json | cut -c1-64)" = c0c81f33a1cc671b6040244d80d47d902ebc7182f77345c1dc1c46f28897c283 ]
cp $F/patched/native_kit/boundaries.py $KC/native_kit/boundaries.py
cp $F/DEPENDENCIES.json $KC/out/DEPENDENCIES.json
cd $KC && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_sources.py

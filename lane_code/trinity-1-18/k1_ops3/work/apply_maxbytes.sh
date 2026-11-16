#!/bin/bash
set -e
KC=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a; F=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_maxbytes; P=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_pre_maxbytes
mkdir -p $P; cp -p $KC/work/k1_cli.py $KC/out/DEPENDENCIES.json $P/
[ "$(sha256sum $F/kit_k1a/work/k1_cli.py | cut -c1-64)" = 3cc7b95ff591d68dc0184ac76d7b706a3b7920c94a2132b0eedd99c1c7e49013 ]
[ "$(sha256sum $F/kit_k1a/out/DEPENDENCIES.json | cut -c1-64)" = b27c28c4fc8c32299dda66d470644c7f6d1b574492fe81a767e601f1b47b91e2 ]
cp $F/kit_k1a/work/k1_cli.py $KC/work/k1_cli.py; cp $F/kit_k1a/out/DEPENDENCIES.json $KC/out/DEPENDENCIES.json
cd $KC && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_sources.py
O=/scratch/jjyeung/k1/run_tower_sam_2; e=$(date +%s)
mv $O/HALTED.json $O/HALTED.reviewed.$e.json; mv $O.preflight.json /scratch/jjyeung/k1/run_tower_sam_2.preflight.run2a.json
ls $O | grep -i halted; ls /scratch/jjyeung/k1 | grep preflight

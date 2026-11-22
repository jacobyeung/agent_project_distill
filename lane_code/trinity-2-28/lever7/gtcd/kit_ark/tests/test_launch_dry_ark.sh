#!/bin/bash
# kit_ark launcher dry run with the ARKit arguments (no GPU, no vnice, no track.py run). Needs the manifest that
# tests/test_dense_ark.py writes (work/test_dense_ark/dense_ark/DENSE_D_ARK.json and its .sha256).
# Checks: --dense/--out reach the inner line (track dir out_ark/track, which a dry run does not create); the env form gives the
# same inner line; the ARKit CPU rehearsal runs the same inner line with only device, --captures and --out changed (a dry run
# names --out work/rehearsal_cpu_ark explicitly; a dry run without --out logs to work/dry_launch as the kit's does); refusals: non-default manifest without --out, ARKit manifest into out/track, ScanNet manifest into
# out_ark/track, a manifest that differs from its .sha256, paths off /scratch; the default inner line equals the sealed kit's
# own dry inner line apart from cd kit_ark and the explicit default --dense.
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; ROOT="$(dirname "$KIT")"; T="$ROOT/work/dry_launch_test_ark"; mkdir -p "$T"
MAN="$ROOT/work/test_dense_ark/dense_ark/DENSE_D_ARK.json"; AOUT="$ROOT/out_ark/track"
[ -f "$MAN" ] && [ -f "$MAN.sha256" ] || { echo "FAIL run tests/test_dense_ark.py first"; exit 1; }
printf '#!/bin/bash\necho "0, 49140, 35000, 8.9"\necho "1, 49140, 3, 8.9"\n' > "$T/smi_free"; chmod +x "$T/smi_free"
run() { local smi="$1" host="$2"; shift 2; GTC_DRY_LAUNCH=1 GTC_WAIT_SECONDS=0 GTC_NVIDIA_SMI="$T/$smi" GTC_HOST="$host" bash "$KIT/launch_gpu.sh" "$@" 2>&1; }
newest() { ls -t "$ROOT"/work/$1_inner_*.sh | head -1; }
OUT_ARK_EXISTED=0; [ -e "$ROOT/out_ark" ] && OUT_ARK_EXISTED=1
o=$(run smi_free trinity-0-13 d --dense "$MAN" --out "$AOUT"); echo "$o" | grep -q "gpu=1 arms=d dense=$MAN out=$AOUT " || { echo FAIL ark_launch; echo "$o"; exit 1; }
GA="$(newest gpu)"; grep -q -- "--device cuda --arms d --out $AOUT --hard-stop 5280 --captures all --dense $MAN\$" "$GA" || { echo FAIL ark_inner; cat "$GA"; exit 1; }
grep -q "^cd \"$KIT\"" "$GA" || { echo FAIL ark_inner_cd; exit 1; }
[ "$OUT_ARK_EXISTED" = 1 ] || [ ! -e "$ROOT/out_ark" ] || { echo FAIL dry_run_created_out_ark; exit 1; }
grep -q '"CHILD".*name=dense_sha256 exit=0' "$ROOT/work/dry_launch/EVENTS.jsonl" || { echo FAIL dense_sha_child; exit 1; }
echo PASS ark_arguments_reach_the_inner_line
sleep 1; o=$(GTCD_DENSE="$MAN" GTCD_TRACK_OUT="$AOUT" run smi_free trinity-0-13 d); echo "$o" | grep -q "dense=$MAN out=$AOUT " || { echo FAIL env; echo "$o"; exit 1; }
GE="$(newest gpu)"; diff <(tail -1 "$GA") <(tail -1 "$GE") > /dev/null || { echo FAIL env_inner_differs; exit 1; }; echo PASS env_form_same_inner_line
o=$(run smi_free trinity-2-28 d --dense "$MAN" --out "$AOUT"); echo "$o" | grep -q "would run bash /data3/shared/scripts/vnice/vnice.sh" || { echo FAIL vnice; exit 1; }; echo PASS ark_off_0-13_under_vnice
sleep 1; o=$(run smi_free trinity-2-28 rehearse-cpu arkitscenes/43828324 --dense "$MAN" --out "$ROOT/work/rehearsal_cpu_ark"); echo "$o" | grep -q "LAUNCH rehearsal device=cpu arms=d captures=arkitscenes/43828324 dense=$MAN out=$ROOT/work/rehearsal_cpu_ark" || { echo FAIL ark_reh; echo "$o"; exit 1; }
CA="$(newest cpu)"
diff <(sed -e 's/CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=[0-9]*/DEV/' -e 's/--device cuda/--device X/' -e 's/--captures all/--captures C/' -e "s#--out $AOUT#--out O#" "$GA") \
     <(sed -e 's/CUDA_VISIBLE_DEVICES= /DEV /' -e 's/--device cpu/--device X/' -e 's#--captures arkitscenes/43828324#--captures C#' -e "s#--out $ROOT/work/rehearsal_cpu_ark#--out O#" "$CA") > /dev/null \
  || { echo FAIL ark_rehearsal_inner_differs; diff "$GA" "$CA"; exit 1; }; echo PASS ark_rehearsal_runs_the_same_inner_line
o=$(run smi_free trinity-0-13 d --dense "$MAN"); echo "$o" | grep -q 'LAUNCH_REFUSED non_default_dense_needs_explicit_out' || { echo FAIL no_out; echo "$o"; exit 1; }
o=$(run smi_free trinity-0-13 d --dense "$MAN" --out "$ROOT/out/track"); echo "$o" | grep -q 'LAUNCH_REFUSED non_scannet_manifest_into_scannet_out_track' || { echo FAIL ark_into_sn; echo "$o"; exit 1; }
o=$(run smi_free trinity-0-13 d --out "$AOUT"); echo "$o" | grep -q 'LAUNCH_REFUSED scannet_manifest_into_out_ark_track' || { echo FAIL sn_into_ark; echo "$o"; exit 1; }
B="$T/tampered"; mkdir -p "$B"; cp "$MAN" "$B/DENSE_D_ARK.json"; echo ' ' >> "$B/DENSE_D_ARK.json"; cp "$MAN.sha256" "$B/"
o=$(run smi_free trinity-0-13 d --dense "$B/DENSE_D_ARK.json" --out "$AOUT"); echo "$o" | grep -q 'LAUNCH_REFUSED dense_manifest_differs_from_its_sha256' || { echo FAIL tampered; echo "$o"; exit 1; }
o=$(run smi_free trinity-0-13 d --dense "$B/absent.json" --out "$AOUT"); echo "$o" | grep -q 'LAUNCH_REFUSED dense_manifest_missing' || { echo FAIL missing; echo "$o"; exit 1; }
o=$(run smi_free trinity-0-13 d --dense "$MAN" --out /tmp/x_track); echo "$o" | grep -q 'LAUNCH_REFUSED track_out_not_on_scratch' || { echo FAIL out_off_scratch; echo "$o"; exit 1; }
o=$(run smi_free trinity-0-13 d --dense /tmp/DENSE_D_ARK.json --out "$AOUT"); echo "$o" | grep -q 'LAUNCH_REFUSED dense_manifest_not_on_scratch' || { echo FAIL dense_off_scratch; echo "$o"; exit 1; }
o=$(run smi_free trinity-0-13 d --dense); echo "$o" | grep -q 'usage' || { echo FAIL dangling_flag; exit 1; }
echo PASS refusals_no_out_crossed_pairs_tampered_missing_off_scratch_dangling_flag
sleep 1; o=$(run smi_free trinity-0-13 d); GD="$(newest gpu)"; sleep 1
o2=$(GTC_DRY_LAUNCH=1 GTC_WAIT_SECONDS=0 GTC_NVIDIA_SMI="$T/smi_free" GTC_HOST=trinity-0-13 bash "$ROOT/kit/launch_gpu.sh" d 2>&1); GK="$(newest gpu)"
[ "$GD" != "$GK" ] || { echo FAIL same_inner_file; exit 1; }
diff <(sed -e "s#^cd \"$KIT\"#cd KIT#" -e "s# --dense $ROOT/dense/DENSE_D.json\$##" "$GD") <(sed -e "s#^cd \"$ROOT/kit\"#cd KIT#" "$GK") > /dev/null \
  || { echo FAIL default_inner_differs_from_sealed_kit; diff "$GD" "$GK"; exit 1; }; echo PASS default_inner_line_equals_the_sealed_kit_apart_from_cd_and_default_dense
echo '{"status": "PASS"}'

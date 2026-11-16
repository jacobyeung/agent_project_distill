# Skip tower generation only when an existing raw cache passes all native pins.
CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/out/geometry.py" tower \
  --dense-manifest "$DENSE_FRAMES" --weights "$G3T_WEIGHTS" --config "$G3T_CONFIG" \
  --device cuda:0 --dest "$RUNROOT/raw_g3t"
CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/out/geometry.py" prepare \
  --raw-tower "$RUNROOT/raw_g3t/RAW_G3T.json" --config "$TRAIN_CONFIG" \
  --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" --step "$STEP" \
  --frames-root "$FRAMES" --device cuda:0 --dest "$RUN/geometry"
GEOMETRY="$RUN/geometry/GEOMETRY_MANIFEST.json"
for ARM in forced_route scripted forced_direct unflagged; do
  "$PY" -I -s "$L/out/routed.py" bind --step "$STEP" --arm "$ARM" --scope supported600 \
    --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" --config "$TRAIN_CONFIG" \
    --geometry "$GEOMETRY" --frames-root "$FRAMES" --dest "$RUN/$ARM"
  CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/out/routed.py" run \
    --dest "$RUN/$ARM" --device cuda:0
done
"$PY" -I -s "$L/out/routed.py" merge --forced-route "$RUN/forced_route" \
  --scripted "$RUN/scripted" --forced-direct "$RUN/forced_direct" --unflagged "$RUN/unflagged" \
  --output "$RUN/ROUTED.json"

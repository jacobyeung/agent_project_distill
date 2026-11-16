for FAMILY in main away forward; do
  "$PY" -I -s "$L/out/direct.py" bind --family "$FAMILY" --step "$STEP" \
    --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" --models "$MODELS" --kit "$KIT" \
    --frames-root "$FRAMES" --dest "$RUN/$FAMILY"
  CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/out/direct.py" launch \
    --dest "$RUN/$FAMILY" --attempt "legs1_m${STEP}_${FAMILY}_a1"
  CUDA_VISIBLE_DEVICES='' "$PY" -I -s "$L/out/direct.py" merge \
    --source "$RUN/$FAMILY" --dest "$RUN/${FAMILY}_merge" --kit "$KIT" \
    --attempt "legs1_m${STEP}_${FAMILY}_a1" \
    --tokenizer-dir "$TOKENIZER" --tokenizer-manifest "$TOKENIZER_MANIFEST"
done
"$PY" -I -s "$L/out/decision.py" --step "$STEP" \
  --leg "$RUN/main_merge" --parent "$L/work/parent_main_merge" \
  --f17 "$RUNROOT/f17_main_merge" --away "$RUN/away_merge" --forward "$RUN/forward_merge" \
  --output "$RUN/DECISION_DIRECT.json"

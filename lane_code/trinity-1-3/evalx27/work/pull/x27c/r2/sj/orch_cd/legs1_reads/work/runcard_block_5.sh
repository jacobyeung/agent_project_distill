"$PY" -I -s "$L/out/decision.py" --step "$STEP" \
  --leg "$RUN/main_merge" --parent "$L/work/parent_main_merge" \
  --f17 "$RUNROOT/f17_main_merge" --away "$RUN/away_merge" --forward "$RUN/forward_merge" \
  --dev858 "$DEV858_PIN" --routed "$RUN/ROUTED.json.pin.json" \
  --output "$RUN/DECISION.json"
# At m200 add: --history "$M100_HISTORY" --official "$OFFICIAL_PIN"

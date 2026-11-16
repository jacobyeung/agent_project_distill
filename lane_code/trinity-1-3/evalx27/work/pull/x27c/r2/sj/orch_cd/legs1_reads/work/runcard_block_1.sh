"$PY" -I -s "$L/work/vendor/r3/adapter.py" bind --cell f17 \
  --kit "$F17KIT" --models "$MODELS" --frames-root "$FRAMES" --dest "$RUNROOT/f17_main"
"$PY" -I -s "$L/work/vendor/r4/adapter.py" bind --cell f17 \
  --payload "$L/work/vendor/r4/DEV_BACKDIR" --kit "$F17KIT" --models "$MODELS" \
  --frames-root "$FRAMES" --dest "$RUNROOT/f17_away"
"$PY" -I -s "$L/work/vendor/r4/adapter.py" bind --cell f17 \
  --payload "$L/work/vendor/r4/DEV_FORWARD_TWINS" --kit "$F17KIT" --models "$MODELS" \
  --frames-root "$FRAMES" --dest "$RUNROOT/f17_forward"
for FAMILY in main away forward; do
  CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/work/vendor/r5/adapter.py" launch \
    --dest "$RUNROOT/f17_$FAMILY" --attempt "f17_${FAMILY}_a1"
  CUDA_VISIBLE_DEVICES='' "$PY" -I -s "$L/work/vendor/r5/adapter.py" merge \
    --source "$RUNROOT/f17_$FAMILY" --dest "$RUNROOT/f17_${FAMILY}_merge" \
    --kit "$F17KIT" --attempt "f17_${FAMILY}_a1"
done

STEP=100
RUN="$RUNROOT/m$STEP"
mkdir -p "$RUN"
: "${EXPORT_URL:?}" "${ARCHIVE_SHA:?}" "${ARTIFACT_SHA:?}" "${PUBLISHED_ROOT:?}" "${ARTIFACT:?}"
curl --fail --location --limit-rate 8M "$EXPORT_URL" --output "$RUN/export.tar"
"$PY" -I -s "$L/out/receive.py" --archive "$RUN/export.tar" \
  --sha256 "$ARCHIVE_SHA" --dest "$PUBLISHED_ROOT"
"$PY" -I -s "$L/out/export_check.py" --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" \
  --step "$STEP" --base "$BASE" --output "$RUN/EXPORT_CHECK.json"

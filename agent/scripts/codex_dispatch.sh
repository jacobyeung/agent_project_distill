#!/usr/bin/env bash

usage() {
  echo "Usage: agent/scripts/codex_dispatch.sh <preset> <dir> <prompt-file> [--net] [--model X] [--effort Y] [--label NAME] [--skip-git-check] [--writable-root DIR ...]" >&2
}

json_escape() {
  local value=$1
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  printf '%s' "$value"
}

cleanup_registry() {
  local tmp_file

  if [[ -n "${CODEX_PID:-}" && -f "$REGISTRY_FILE" ]]; then
    tmp_file="${REGISTRY_FILE}.tmp.$$"
    if awk -F '|' -v pid="$CODEX_PID" -v receipt_dir="$RECEIPT_DIR" \
      '$1 != pid || $4 != receipt_dir' "$REGISTRY_FILE" > "$tmp_file"; then
      mv "$tmp_file" "$REGISTRY_FILE"
    fi
    rm -f "$tmp_file"
  fi
}

if [[ $# -lt 3 || "$1" == --* || "$2" == --* || "$3" == --* ]]; then
  usage
  exit 2
fi

PRESET=$1
DIR=$2
PROMPT_FILE=$3
shift 3

case "$PRESET" in
  review)
    SANDBOX=read-only
    MODEL=gpt-6-astra
    EFFORT=high
    EFFORT_SET=true
    ;;
  implement)
    SANDBOX=workspace-write
    MODEL=gpt-5.6-sol
    EFFORT=high
    EFFORT_SET=true
    ;;
  mech)
    SANDBOX=workspace-write
    MODEL=gpt-5.6-terra
    EFFORT=
    EFFORT_SET=false
    ;;
  *)
    echo "Unknown preset: $PRESET (expected: review|implement|mech)" >&2
    exit 2
    ;;
esac

if [[ ! -d "$DIR" ]]; then
  echo "Directory does not exist: $DIR" >&2
  exit 2
fi

if [[ ! -f "$PROMPT_FILE" || ! -r "$PROMPT_FILE" ]]; then
  echo "Prompt file is not readable: $PROMPT_FILE" >&2
  exit 2
fi

DIR=$(cd "$DIR" && pwd -P)
NET=false
SKIP_GIT=false
LABEL=$(basename "$PROMPT_FILE")
WRITABLE_ROOTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --net)
      NET=true
      shift
      ;;
    --writable-root)
      if [[ $# -lt 2 || ! -d "$2" ]]; then
        echo "Missing or nonexistent directory for --writable-root" >&2
        exit 2
      fi
      WRITABLE_ROOTS+=("$(cd "$2" && pwd -P)")
      shift 2
      ;;
    --model)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --model" >&2
        exit 2
      fi
      MODEL=$2
      shift 2
      ;;
    --effort)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --effort" >&2
        exit 2
      fi
      EFFORT=$2
      EFFORT_SET=true
      shift 2
      ;;
    --label)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --label" >&2
        exit 2
      fi
      LABEL=$2
      shift 2
      ;;
    --skip-git-check)
      SKIP_GIT=true
      shift
      ;;
    *)
      echo "Unknown flag: $1" >&2
      exit 2
      ;;
  esac
done

if ! git -C "$DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  SKIP_GIT=true
fi

if grep -qE 'setsid|nohup' "$PROMPT_FILE"; then
  echo "WARNING: prompt file mentions setsid/nohup — detached background processes die when this" >&2
  echo "sandboxed codex exec call returns; plan long-running launches accordingly." >&2
fi

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
RECEIPT_DIR="$REPO_ROOT/agent/scratch/codex_runs/${TIMESTAMP}_${LABEL}"
REGISTRY_FILE="$REPO_ROOT/agent/scratch/codex_runs/RUNNING.registry"
SPEND_LOG="$REPO_ROOT/agent/scratch/codex_runs/CODEX_SPEND.log"

if ! mkdir -p "$RECEIPT_DIR"; then
  echo "Could not create receipt directory: $RECEIPT_DIR" >&2
  exit 1
fi

if ! cp "$PROMPT_FILE" "$RECEIPT_DIR/prompt.md"; then
  echo "Could not copy prompt file to receipt directory" >&2
  exit 1
fi

codex_args=(exec -m "$MODEL")
if [[ "$EFFORT_SET" == true ]]; then
  codex_args+=(-c "model_reasoning_effort=$EFFORT")
fi
codex_args+=(-s "$SANDBOX" -C "$DIR")
if [[ "$NET" == true ]]; then
  codex_args+=(-c "sandbox_workspace_write.network_access=true")
fi
if [[ ${#WRITABLE_ROOTS[@]} -gt 0 ]]; then
  ROOTS_TOML=""
  for r in "${WRITABLE_ROOTS[@]}"; do
    ROOTS_TOML+="\"${r}\","
  done
  codex_args+=(-c "sandbox_workspace_write.writable_roots=[${ROOTS_TOML%,}]")
fi
if [[ "$SKIP_GIT" == true ]]; then
  codex_args+=(--skip-git-repo-check)
fi
codex_args+=(-o "$RECEIPT_DIR/final_message.md" -)

CODEX_PID=
trap cleanup_registry EXIT

START_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_SECONDS=$(date -u +%s)
codex "${codex_args[@]}" < "$PROMPT_FILE" > "$RECEIPT_DIR/transcript.log" 2>&1 &
CODEX_PID=$!
printf '%s|%s|%s|%s\n' "$CODEX_PID" "$LABEL" "$START_TIME" "$RECEIPT_DIR" >> "$REGISTRY_FILE"

wait "$CODEX_PID"
EXIT_CODE=$?
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
END_SECONDS=$(date -u +%s)
WALL_SECONDS=$((END_SECONDS - START_SECONDS))

printf '%s | %s | %s | %s | %s | %s | %s\n' \
  "$START_TIME" "$PRESET" "$MODEL" "$EFFORT" "$LABEL" "$WALL_SECONDS" "$EXIT_CODE" >> "$SPEND_LOG"

{
  printf '{\n'
  printf '  "preset": "%s",\n' "$(json_escape "$PRESET")"
  printf '  "model": "%s",\n' "$(json_escape "$MODEL")"
  printf '  "effort": "%s",\n' "$(json_escape "$EFFORT")"
  printf '  "dir": "%s",\n' "$(json_escape "$DIR")"
  printf '  "label": "%s",\n' "$(json_escape "$LABEL")"
  printf '  "exit_code": %s,\n' "$EXIT_CODE"
  printf '  "start_time": "%s",\n' "$START_TIME"
  printf '  "end_time": "%s",\n' "$END_TIME"
  printf '  "wall_seconds": %s,\n' "$WALL_SECONDS"
  printf '  "pid": %s\n' "$CODEX_PID"
  printf '}\n'
} > "$RECEIPT_DIR/meta.json"

exit "$EXIT_CODE"

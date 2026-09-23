#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
TMP_DIR="/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/_selftest_codex_dispatch_${TIMESTAMP}"
TMP_BRANCH="codex-dispatch-worktree-selftest-${TIMESTAMP}"
PROMPT_FILE="$TMP_DIR/codex_dispatch_selftest_prompt.md"
WORKTREE_ADDED=false
FAIL_REASON=""

cleanup() {
  local prior_status=$?
  local cleanup_failed=false

  set +e
  if [[ "$WORKTREE_ADDED" == true ]]; then
    git -C "$REPO_ROOT" worktree remove --force "$TMP_DIR"
    if [[ $? -ne 0 ]]; then
      cleanup_failed=true
      FAIL_REASON="could not remove temporary worktree $TMP_DIR"
    fi
  fi
  if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/$TMP_BRANCH"; then
    git -C "$REPO_ROOT" branch -D "$TMP_BRANCH"
    if [[ $? -ne 0 ]]; then
      cleanup_failed=true
      FAIL_REASON="could not delete temporary branch $TMP_BRANCH"
    fi
  fi

  if [[ "$prior_status" -ne 0 || -n "$FAIL_REASON" || "$cleanup_failed" == true ]]; then
    printf 'SELFTEST FAIL: %s\n' "${FAIL_REASON:-unexpected command failure}"
    exit 1
  fi

  printf 'SELFTEST PASS\n'
  exit 0
}
trap cleanup EXIT

if ! git -C "$REPO_ROOT" worktree add "$TMP_DIR" -b "$TMP_BRANCH" HEAD; then
  FAIL_REASON="could not create temporary worktree"
  exit 1
fi
WORKTREE_ADDED=true

printf '%s\n' \
  'Create SELFTEST_OK.txt containing exactly one line: OK.' \
  "Run git add SELFTEST_OK.txt && git commit -m 'selftest: worktree commit'." \
  'Do not create, modify, stage, or commit anything else.' > "$PROMPT_FILE"

if ! "$REPO_ROOT/agent/scripts/codex_dispatch.sh" mech "$TMP_DIR" "$PROMPT_FILE" \
  --label "worktree_selftest_${TIMESTAMP}"; then
  FAIL_REASON="codex_dispatch.sh exited nonzero"
  exit 1
fi

if [[ "$(git -C "$TMP_DIR" log -1 --format=%s)" != "selftest: worktree commit" ]]; then
  FAIL_REASON="temporary branch does not contain the expected commit message"
  exit 1
fi
if [[ "$(git -C "$TMP_DIR" show HEAD:SELFTEST_OK.txt)" != "OK" ]]; then
  FAIL_REASON="SELFTEST_OK.txt does not contain OK"
  exit 1
fi
